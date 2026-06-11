<script setup lang="ts">
import { nextTick, ref } from 'vue'
import { useQueryClient } from '@tanstack/vue-query'

import { createReply } from '@/api/threads'
import { useCaptcha } from '@/composables/useCaptcha'
import { appendPostToThread, threadQueryKey } from '@/composables/useThread'
import type { ThreadDetailResponse } from '@/api/types'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseInput from '@/components/ui/BaseInput.vue'
import CaptchaWidget from '@/components/ui/CaptchaWidget.vue'
import MarkupTextarea from '@/components/ui/MarkupTextarea.vue'

const props = defineProps<{
  slug: string
  threadId: number
}>()

const queryClient = useQueryClient()

const formElement = ref<HTMLFormElement | null>(null)

const { data: captcha, isPending: captchaPending, isError: captchaError, refetch: refreshCaptcha } = useCaptcha()

const name = ref('')
const body = ref('')
const sage = ref(false)
const captchaAnswer = ref('')
const selectedFiles = ref<File[]>([])
const isSubmitting = ref(false)
const submitError = ref<string | null>(null)

function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files) {
    selectedFiles.value = Array.from(input.files).slice(0, 10)
  }
}

// quote a post: drop a >>N reference on its own line at the end of the body and
// focus the textarea so the poster can keep typing. called from ThreadView when
// a post number is clicked.
async function quote(postNumber: number) {
  const base = body.value && !body.value.endsWith('\n') ? `${body.value}\n` : body.value
  body.value = `${base}>>${postNumber}\n`
  await nextTick()
  formElement.value?.querySelector<HTMLTextAreaElement>('#reply-body')?.focus()
}

defineExpose({ quote })

function resetForm() {
  name.value = ''
  body.value = ''
  sage.value = false
  captchaAnswer.value = ''
  selectedFiles.value = []
}

async function onSubmit() {
  submitError.value = null

  if (!body.value.trim() && selectedFiles.value.length === 0) {
    submitError.value = 'A reply needs a body or a file.'
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
    const post = await createReply(
      props.slug,
      props.threadId,
      {
        name: name.value || undefined,
        body: body.value || undefined,
        sage: sage.value,
      },
      selectedFiles.value,
      captcha.value.token,
      captchaAnswer.value.trim(),
    )
    // append the new post to the cached thread so it shows without a refetch
    queryClient.setQueryData<ThreadDetailResponse>(
      threadQueryKey(props.slug, props.threadId),
      (old) => appendPostToThread(old, post),
    )
    resetForm()
    await refreshCaptcha()
  } catch (error: unknown) {
    const detail = (error as Record<string, unknown>)?.detail
    submitError.value = typeof detail === 'string' ? detail : 'Failed to post reply.'
    await refreshCaptcha()
    captchaAnswer.value = ''
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <form
    ref="formElement"
    class="flex flex-col gap-4 rounded-card border border-border bg-surface p-6 shadow-card"
    @submit.prevent="onSubmit"
  >
    <h2 class="flex items-center gap-2.5 text-2xl font-extrabold">
      <span class="text-gold-2" aria-hidden="true">↩</span> Reply
    </h2>

    <div class="flex flex-col gap-1.5">
      <label for="reply-name" class="text-[13px] font-bold">Name</label>
      <BaseInput id="reply-name" v-model="name" placeholder="Anonymous" maxlength="100" />
    </div>

    <div class="flex flex-col gap-1.5">
      <label for="reply-body" class="text-[13px] font-bold">Body</label>
      <MarkupTextarea
        id="reply-body"
        v-model="body"
        rows="4"
        maxlength="5000"
        placeholder="Reply body…"
      />
    </div>

    <div class="flex flex-col gap-1.5">
      <label for="reply-files" class="text-[13px] font-bold">
        Files <span class="ml-1 text-xs font-normal text-text-muted">(optional)</span>
      </label>
      <input
        id="reply-files"
        type="file"
        accept="image/*,video/*"
        multiple
        class="text-sm text-text-muted file:mr-3 file:cursor-pointer file:rounded-field file:border file:border-dashed file:border-border file:bg-surface file:px-3.5 file:py-2 file:text-[13px] file:font-semibold file:text-text hover:file:border-gold hover:file:text-accent"
        @change="onFileChange"
      />
    </div>

    <label class="flex items-center gap-2 text-[13.5px]">
      <input v-model="sage" type="checkbox" class="h-4 w-4 accent-gold" />
      <b>sage</b> <span class="text-text-muted">(don't bump the thread)</span>
    </label>

    <CaptchaWidget
      v-model="captchaAnswer"
      :captcha="captcha"
      :is-pending="captchaPending"
      :is-error="captchaError"
      @refresh="refreshCaptcha"
    />

    <p v-if="submitError" class="text-sm text-danger">{{ submitError }}</p>

    <div class="mt-1 flex items-center gap-3.5">
      <BaseButton type="submit" variant="primary" :disabled="isSubmitting">
        {{ isSubmitting ? 'Posting…' : 'Post reply' }}
      </BaseButton>
      <BaseButton type="button" variant="link" size="sm" :disabled="isSubmitting" @click="resetForm">
        Clear
      </BaseButton>
    </div>
  </form>
</template>
