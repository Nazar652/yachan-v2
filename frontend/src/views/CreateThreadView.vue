<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useQueryClient } from '@tanstack/vue-query'

import { createThread } from '@/api/threads'
import { useCaptcha } from '@/composables/useCaptcha'
import { threadsQueryKey } from '@/composables/useThreads'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseInput from '@/components/ui/BaseInput.vue'
import CaptchaWidget from '@/components/ui/CaptchaWidget.vue'
import MarkupTextarea from '@/components/ui/MarkupTextarea.vue'

const route = useRoute()
const router = useRouter()
const queryClient = useQueryClient()

const slug = computed(() => route.params.slug as string)

const { data: captcha, isPending: captchaPending, isError: captchaError, refetch: refreshCaptcha } = useCaptcha()

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

  if (!captchaAnswer.value.trim()) {
    submitError.value = 'Please enter the captcha answer.'
    return
  }

  if (!captcha.value) {
    submitError.value = 'Captcha not loaded yet.'
    return
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
      captcha.value.token,
      captchaAnswer.value.trim(),
    )
    await queryClient.invalidateQueries({ queryKey: threadsQueryKey(slug.value) })
    await router.push({ name: 'thread', params: { slug: slug.value, id: thread.id } })
  } catch (error: unknown) {
    const detail = (error as Record<string, unknown>)?.detail
    submitError.value = typeof detail === 'string' ? detail : 'Failed to create thread.'
    await refreshCaptcha()
    captchaAnswer.value = ''
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="max-w-2xl mx-auto px-4 py-6">
    <div class="mb-4 text-sm text-secondary">
      <RouterLink :to="`/${slug}`" class="hover:text-accent">← /{{ slug }}/</RouterLink>
    </div>

    <h1 class="text-xl font-semibold mb-6">New thread</h1>

    <form class="flex flex-col gap-4" @submit.prevent="onSubmit">
      <div class="flex flex-col gap-1">
        <label for="title" class="text-sm font-medium">Title</label>
        <BaseInput id="title" v-model="title" placeholder="Thread title (optional)" maxlength="150" />
      </div>

      <div class="flex flex-col gap-1">
        <label for="name" class="text-sm font-medium">Name</label>
        <BaseInput id="name" v-model="name" placeholder="Anonymous" maxlength="100" />
      </div>

      <div class="flex flex-col gap-1">
        <label for="body" class="text-sm font-medium">Body</label>
        <MarkupTextarea
          id="body"
          v-model="body"
          rows="6"
          maxlength="5000"
          placeholder="Post body…"
        />
      </div>

      <div class="flex flex-col gap-1">
        <label for="files" class="text-sm font-medium">
          Image <span class="text-red-500">*</span>
          <span class="text-secondary font-normal ml-1">(required for OP)</span>
        </label>
        <input
          id="files"
          type="file"
          accept="image/*"
          multiple
          class="text-sm"
          @change="onFileChange"
        />
        <p v-if="selectedFiles.length && !hasImage" class="text-xs text-red-500">
          OP post requires at least one image file.
        </p>
      </div>

      <CaptchaWidget
        v-model="captchaAnswer"
        :captcha="captcha"
        :is-pending="captchaPending"
        :is-error="captchaError"
        @refresh="refreshCaptcha"
      />

      <p v-if="submitError" class="text-sm text-red-500">{{ submitError }}</p>

      <div class="flex gap-3 mt-2">
        <BaseButton type="submit" variant="primary" :disabled="isSubmitting">
          {{ isSubmitting ? 'Posting…' : 'Post thread' }}
        </BaseButton>
        <BaseButton
          type="button"
          variant="ghost"
          @click="router.push(`/${slug}`)"
        >
          Cancel
        </BaseButton>
      </div>
    </form>
  </div>
</template>
