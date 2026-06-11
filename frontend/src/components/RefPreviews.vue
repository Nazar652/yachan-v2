<script setup lang="ts">
import { computed } from 'vue'

import { useOwnPosts } from '@/composables/useOwnPosts'
import { useRefPreviews } from '@/composables/useRefPreviews'
import type { AttachmentResponse, PostResponse } from '@/api/types'
import PostBody from '@/components/ui/PostBody.vue'

const props = defineProps<{ posts: PostResponse[]; slug: string }>()

const emit = defineEmits<{ navigate: [postNumber: number] }>()

const { ownNumbers, isOwn } = useOwnPosts(() => props.slug)

const postByNumber = computed(() => {
  const map = new Map<number, PostResponse>()
  for (const post of props.posts) map.set(post.post_number, post)
  return map
})

const { previews, clear } = useRefPreviews((postNumber) => postByNumber.value.get(postNumber))

function imageThumbs(post: PostResponse): AttachmentResponse[] {
  return (post.attachments ?? []).filter(
    (attachment) => attachment.media_type === 'image' || attachment.media_type === 'gif',
  )
}

function thumbSrc(attachment: AttachmentResponse): string {
  return attachment.media_type === 'gif' ? attachment.url : (attachment.thumbnail_url ?? attachment.url)
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString()
}

// clicking a ref inside a preview navigates to the post in the thread; drop the
// stack so the previews don't hang around after the jump
function onNavigate(postNumber: number) {
  clear()
  emit('navigate', postNumber)
}
</script>

<template>
  <Teleport to="body">
    <div
      v-for="preview in previews"
      :key="preview.level"
      class="ref-preview"
      :data-level="preview.level"
      :style="{ top: `${preview.top}px`, left: `${preview.left}px` }"
    >
      <article
        class="rounded-card border p-3 shadow-deep"
        :class="preview.post.is_op
          ? 'border-[color-mix(in_srgb,var(--color-gold)_32%,var(--color-border))] bg-surface-2'
          : 'border-border bg-surface'"
      >
        <div class="mb-1.5 flex flex-wrap items-baseline gap-x-2 gap-y-1 text-[13px]">
          <span class="font-bold text-greentext">{{ preview.post.name }}</span>
          <span v-if="preview.post.tripcode" class="font-mono text-text-muted">{{ preview.post.tripcode }}</span>
          <span class="font-mono text-xs text-text-muted">{{ formatDate(preview.post.created_at) }}</span>
          <span class="font-mono text-xs text-text-muted">No.{{ preview.post.post_number }}</span>
          <span v-if="isOwn(preview.post.post_number)" class="post-you font-mono text-xs font-bold">(You)</span>
        </div>

        <div v-if="imageThumbs(preview.post).length" class="mb-2 flex flex-wrap gap-2">
          <img
            v-for="att in imageThumbs(preview.post)"
            :key="att.id"
            :src="thumbSrc(att)"
            :alt="att.original_name"
            class="max-h-28 max-w-[120px] rounded-field border border-border object-contain"
          />
        </div>

        <PostBody
          v-if="preview.post.body_html"
          :html="preview.post.body_html"
          :own-numbers="ownNumbers"
          class="text-sm"
          @navigate="onNavigate"
        />
        <div v-else-if="preview.post.body" class="whitespace-pre-wrap text-sm">{{ preview.post.body }}</div>
        <div v-else class="text-sm italic text-text-muted">(no text)</div>
      </article>
    </div>
  </Teleport>
</template>

<style scoped>
.ref-preview {
  position: fixed;
  z-index: 50;
  width: max-content;
  max-width: 480px;
  animation: ref-preview-in 0.12s ease;
}
@keyframes ref-preview-in {
  from { opacity: 0; transform: translateY(-3px); }
  to   { opacity: 1; transform: translateY(0); }
}
</style>
