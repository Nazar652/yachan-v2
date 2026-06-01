<script setup lang="ts">
import { computed, toRef } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { useThread } from '@/composables/useThread'
import type { AttachmentResponse } from '@/api/types'
import ReplyForm from '@/components/ReplyForm.vue'

const route = useRoute()
const slug = computed(() => route.params.slug as string)
const threadId = computed(() => Number(route.params.id))

const { data: thread, isPending, isError } = useThread(
  toRef(slug),
  toRef(threadId),
)

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString()
}

function formatSize(bytes: number | null | undefined): string {
  if (!bytes) return ''
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

// render post body_html: highlight >>N backlinks and greentext
function processHtml(html: string | null | undefined): string {
  if (!html) return ''
  return html
}

function isImage(attachment: AttachmentResponse): boolean {
  return attachment.media_type === 'image'
}
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 py-6">
    <div class="mb-4 text-sm text-secondary">
      <RouterLink :to="`/${slug}`" class="hover:text-accent">← /{{ slug }}/</RouterLink>
    </div>

    <div v-if="isPending" class="text-secondary py-8 text-center">Loading…</div>

    <div v-else-if="isError" class="text-red-500 py-8 text-center">
      Failed to load thread
    </div>

    <template v-else-if="thread">
      <div class="mb-4 flex items-center gap-2">
        <h1 class="text-xl font-semibold">
          {{ thread.title ?? '(no title)' }}
        </h1>
        <span v-if="thread.is_sticky" title="Sticky">📌</span>
        <span v-if="thread.is_locked" title="Locked">🔒</span>
        <span class="ml-auto text-sm text-secondary">{{ thread.reply_count }} replies</span>
      </div>

      <div class="flex flex-col gap-6">
        <article
          v-for="post in thread.posts ?? []"
          :id="`post-${post.post_number}`"
          :key="post.id"
          class="border border-border rounded p-4"
          :class="{ 'bg-surface': post.is_op }"
        >
          <!-- post header -->
          <div class="flex flex-wrap items-baseline gap-x-2 gap-y-1 text-sm mb-2">
            <span class="font-semibold text-accent">{{ post.name }}</span>
            <span v-if="post.tripcode" class="font-mono text-secondary">{{ post.tripcode }}</span>
            <span class="text-secondary">{{ formatDate(post.created_at) }}</span>
            <span class="font-mono text-secondary">No.{{ post.post_number }}</span>
            <span v-if="post.is_edited" class="text-xs text-secondary italic">(edited)</span>
            <span v-if="post.sage" class="text-xs text-secondary">sage</span>
          </div>

          <!-- attachments -->
          <div
            v-if="post.attachments && post.attachments.length"
            class="flex flex-wrap gap-3 mb-3"
          >
            <a
              v-for="att in post.attachments"
              :key="att.id"
              :href="att.url"
              target="_blank"
              rel="noopener"
              class="block"
            >
              <img
                v-if="isImage(att)"
                :src="att.thumbnail_url ?? att.url"
                :alt="att.original_name"
                :title="`${att.original_name} (${formatSize(att.size_bytes)})`"
                class="max-h-32 max-w-32 object-contain rounded border border-border"
              />
              <div
                v-else
                class="flex items-center gap-1 text-xs text-accent underline"
              >
                📎 {{ att.original_name }}
              </div>
            </a>
          </div>

          <!-- body -->
          <div
            v-if="post.body_html"
            class="prose prose-sm post-body"
            v-html="processHtml(post.body_html)"
          />
          <div v-else-if="post.body" class="text-sm whitespace-pre-wrap">{{ post.body }}</div>
        </article>
      </div>

      <div class="mt-6">
        <p v-if="thread.is_locked" class="text-sm text-secondary italic py-4 text-center">
          🔒 This thread is locked.
        </p>
        <ReplyForm v-else :slug="slug" :thread-id="threadId" />
      </div>
    </template>
  </div>
</template>

<style scoped>
.post-body :deep(blockquote),
.post-body :deep(.greentext) {
  color: var(--color-greentext, #789922);
}

.post-body :deep(a.post-ref) {
  color: var(--color-accent);
  text-decoration: underline;
}
</style>

