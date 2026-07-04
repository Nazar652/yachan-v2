<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useQueryClient } from '@tanstack/vue-query'

import { createThread } from '@/api/threads'
import { useCaptcha } from '@/composables/useCaptcha'
import { useOwnPosts } from '@/composables/useOwnPosts'
import { threadsQueryKey } from '@/composables/useThreads'
import { useAuthStore } from '@/stores/auth'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseInput from '@/components/ui/BaseInput.vue'
import CaptchaWidget from '@/components/ui/CaptchaWidget.vue'
import MarkupTextarea from '@/components/ui/MarkupTextarea.vue'

const route = useRoute()
const router = useRouter()
const queryClient = useQueryClient()
const authStore = useAuthStore()

const slug = computed(() => route.params.slug as string)
const { markOwn } = useOwnPosts(slug)

// admins post without a captcha, so skip fetching a challenge they'll never see
const { data: captcha, isPending: captchaPending, isError: captchaError, refetch: refreshCaptcha } = useCaptcha(
  computed(() => !authStore.isAdmin),
)

const title = ref('')
const name = ref('')
const body = ref('')
const captchaAnswer = ref('')
const selectedFiles = ref<File[]>([])
const isSubmitting = ref(false)
const submitError = ref<string | null>(null)

const imageFiles = computed(() => selectedFiles.value.filter((f) => f.type.startsWith('image/')))
const hasImage = computed(() => imageFiles.value.length > 0)

function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files) {
    selectedFiles.value = Array.from(input.files).slice(0, 10)
  }
}

async function onSubmit() {
  submitError.value = null

  if (!hasImage.value) {
    submitError.value = 'OP post must include at least one image.'
    return
  }

  if (!authStore.isAdmin) {
    if (!captchaAnswer.value.trim()) {
      submitError.value = 'Please enter the captcha answer.'
      return
    }

    if (!captcha.value) {
      submitError.value = 'Captcha not loaded yet.'
      return
    }
  }

  isSubmitting.value = true
  try {
    const thread = await createThread(
      slug.value,
      {
        title: title.value || undefined,
        name: name.value || undefined,
        body: body.value || undefined,
      },
      selectedFiles.value,
      authStore.isAdmin ? null : captcha.value!.token,
      authStore.isAdmin ? null : captchaAnswer.value.trim(),
      authStore.isAdmin ? authStore.token : null,
    )
    // remember the OP as one of "your" posts so it renders a (You) tag
    if (thread.posts?.[0]) markOwn(thread.posts[0].post_number)
    await queryClient.invalidateQueries({ queryKey: threadsQueryKey(slug.value) })
    await router.push({ name: 'thread', params: { slug: slug.value, id: thread.id } })
  } catch (error: unknown) {
    const detail = (error as Record<string, unknown>)?.detail
    submitError.value = typeof detail === 'string' ? detail : 'Failed to create thread.'
    if (!authStore.isAdmin) {
      await refreshCaptcha()
      captchaAnswer.value = ''
    }
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-2xl py-4">
    <RouterLink
      :to="`/${slug}`"
      class="mb-1 inline-flex cursor-pointer items-center gap-1.5 rounded-field px-1.5 py-1 font-mono text-[13px] text-accent transition-all hover:gap-2.5 hover:bg-surface-3 hover:text-accent-hover"
    >
      ‹ /{{ slug }}/
    </RouterLink>

    <div class="mb-4 flex items-baseline gap-3">
      <h1 class="text-3xl font-extrabold tracking-tight">New thread</h1>
      <span class="ml-auto font-mono text-[13px] text-text-muted">posting to /{{ slug }}/</span>
    </div>

    <form
      class="flex flex-col gap-4 rounded-card border border-border bg-surface p-6 shadow-card"
      @submit.prevent="onSubmit"
    >
      <div class="flex flex-col gap-1.5">
        <label for="title" class="text-[13px] font-bold">
          Title <span class="ml-1 text-xs font-normal text-text-muted">(optional)</span>
        </label>
        <BaseInput id="title" v-model="title" placeholder="Thread title" maxlength="150" />
      </div>

      <div class="flex flex-col gap-1.5">
        <label for="name" class="text-[13px] font-bold">Name</label>
        <BaseInput id="name" v-model="name" placeholder="Anonymous" maxlength="100" />
      </div>

      <div class="flex flex-col gap-1.5">
        <label for="body" class="text-[13px] font-bold">Body</label>
        <MarkupTextarea
          id="body"
          v-model="body"
          rows="6"
          maxlength="5000"
          placeholder="Post body…"
        />
      </div>

      <div class="flex flex-col gap-1.5">
        <label for="files" class="text-[13px] font-bold">
          Image <span class="text-danger">*</span>
          <span class="ml-1 text-xs font-normal text-text-muted">(required for OP)</span>
        </label>
        <input
          id="files"
          type="file"
          accept="image/*"
          multiple
          class="text-sm text-text-muted file:mr-3 file:cursor-pointer file:rounded-field file:border file:border-dashed file:border-border file:bg-surface file:px-3.5 file:py-2 file:text-[13px] file:font-semibold file:text-text hover:file:border-gold hover:file:text-accent"
          @change="onFileChange"
        />
        <p v-if="selectedFiles.length && !hasImage" class="text-xs text-danger">
          OP post requires at least one image file.
        </p>
      </div>

      <CaptchaWidget
        v-if="!authStore.isAdmin"
        v-model="captchaAnswer"
        :captcha="captcha"
        :is-pending="captchaPending"
        :is-error="captchaError"
        @refresh="refreshCaptcha"
      />

      <p v-if="submitError" class="text-sm text-danger">{{ submitError }}</p>

      <div class="mt-1 flex items-center gap-3.5">
        <BaseButton type="submit" variant="primary" :disabled="isSubmitting">
          {{ isSubmitting ? 'Posting…' : '+ Post thread' }}
        </BaseButton>
        <BaseButton type="button" variant="link" size="sm" @click="router.push(`/${slug}`)">
          Cancel
        </BaseButton>
      </div>
    </form>
  </div>
</template>
