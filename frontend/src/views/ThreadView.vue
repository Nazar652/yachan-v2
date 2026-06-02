<script setup lang="ts">
import { computed, ref, toRef } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { useThread } from '@/composables/useThread'
import { useThreadWs } from '@/composables/useThreadWs'
import { useModeration } from '@/composables/useModeration'
import { useAuthStore } from '@/stores/auth'
import type { AttachmentResponse } from '@/api/types'
import ReplyForm from '@/components/ReplyForm.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseInput from '@/components/ui/BaseInput.vue'

const route = useRoute()
const slug = computed(() => route.params.slug as string)
const threadId = computed(() => Number(route.params.id))

const { data: thread, isPending, isError } = useThread(
  toRef(slug),
  toRef(threadId),
)

// stream live new_post / post_edited events into the thread cache
useThreadWs(slug, threadId)

const auth = useAuthStore()
const moderation = useModeration(slug, threadId)

// per-post inline ban form: holds which post is being banned and the reason
const banningPost = ref<number | null>(null)
const banReason = ref('')

async function onToggleLock() {
  if (thread.value) await moderation.setLocked(!thread.value.is_locked)
}

async function onToggleSticky() {
  if (thread.value) await moderation.setSticky(!thread.value.is_sticky)
}

async function onDelete(postNumber: number) {
  await moderation.removePost(postNumber)
}

function onStartBan(postNumber: number) {
  banningPost.value = postNumber
  banReason.value = ''
}

function onCancelBan() {
  banningPost.value = null
  banReason.value = ''
}

async function onConfirmBan(postNumber: number) {
  await moderation.ban(postNumber, { reason: banReason.value || null })
  onCancelBan()
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString()
}

function formatSize(bytes: number | null | undefined): string {
  if (!bytes) return ''
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
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

      <div v-if="auth.isAuthenticated" class="mb-4 flex gap-2">
        <BaseButton variant="ghost" size="sm" @click="onToggleLock">
          {{ thread.is_locked ? 'Unlock' : 'Lock' }}
        </BaseButton>
        <BaseButton variant="ghost" size="sm" @click="onToggleSticky">
          {{ thread.is_sticky ? 'Unsticky' : 'Sticky' }}
        </BaseButton>
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

          <!-- body: server-rendered html (backlinks/greentext) styled via scoped css -->
          <div
            v-if="post.body_html"
            class="prose prose-sm post-body"
            v-html="post.body_html"
          />
          <div v-else-if="post.body" class="text-sm whitespace-pre-wrap">{{ post.body }}</div>

          <!-- mod controls (only when logged in as a mod) -->
          <div v-if="auth.isAuthenticated" class="mt-3 flex flex-col gap-2 border-t border-border pt-2">
            <div class="flex gap-2">
              <BaseButton variant="danger" size="sm" @click="onDelete(post.post_number)">Delete</BaseButton>
              <BaseButton variant="ghost" size="sm" @click="onStartBan(post.post_number)">Ban</BaseButton>
            </div>
            <div v-if="banningPost === post.post_number" class="flex items-center gap-2">
              <BaseInput v-model="banReason" placeholder="Ban reason (optional)" />
              <BaseButton variant="danger" size="sm" @click="onConfirmBan(post.post_number)">Confirm ban</BaseButton>
              <BaseButton variant="ghost" size="sm" @click="onCancelBan">Cancel</BaseButton>
            </div>
          </div>
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

