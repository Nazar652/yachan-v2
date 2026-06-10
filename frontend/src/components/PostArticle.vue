<script setup lang="ts">
import { computed, ref, toRef } from 'vue'

import { useModeration } from '@/composables/useModeration'
import { useEditPost } from '@/composables/useEditPost'
import { usePostHistory } from '@/composables/usePostHistory'
import { numberCodeLines } from '@/utils/postHtml'
import { useAuthStore } from '@/stores/auth'
import type { AttachmentResponse, PostResponse } from '@/api/types'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseInput from '@/components/ui/BaseInput.vue'
import MarkupTextarea from '@/components/ui/MarkupTextarea.vue'

const props = defineProps<{
  post: PostResponse
  slug: string
  threadId: number
}>()

const auth = useAuthStore()
const moderation = useModeration(() => props.slug, () => props.threadId)
const { editPost } = useEditPost(() => props.slug, () => props.threadId)

const isEditing = ref(false)
const editDraft = ref('')
const editError = ref<string | null>(null)
const isSaving = ref(false)

function startEdit() {
  isEditing.value = true
  editDraft.value = props.post.body ?? ''
  editError.value = null
}

function cancelEdit() {
  isEditing.value = false
  editError.value = null
}

async function saveEdit() {
  isSaving.value = true
  editError.value = null

  try {
    await editPost(props.post.post_number, editDraft.value.trim() || null)
    isEditing.value = false
  } catch (error: unknown) {
    const detail = (error as Record<string, unknown>)?.detail
    editError.value = typeof detail === 'string' ? detail : 'Failed to edit post.'
  } finally {
    isSaving.value = false
  }
}

// show-original: fetch the pre-edit body lazily and only while the button is hovered
const showOriginal = ref(false)
const { data: original } = usePostHistory(toRef(props, 'slug'), props.post.post_number, showOriginal)

const bodyHtml = computed(() => (props.post.body_html ? numberCodeLines(props.post.body_html) : null))
const originalBodyHtml = computed(() =>
  original.value?.original_body_html ? numberCodeLines(original.value.original_body_html) : null,
)

const isBanning = ref(false)
const banReason = ref('')

async function onDelete() {
  await moderation.removePost(props.post.post_number)
}

function startBan() {
  isBanning.value = true
  banReason.value = ''
}

function cancelBan() {
  isBanning.value = false
  banReason.value = ''
}

async function confirmBan() {
  await moderation.ban(props.post.post_number, { reason: banReason.value || null })
  cancelBan()
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
  return attachment.media_type === 'image' || attachment.media_type === 'gif'
}

function isVideo(attachment: AttachmentResponse): boolean {
  return attachment.media_type === 'video'
}

function imageSrc(attachment: AttachmentResponse): string {
  return attachment.media_type === 'gif'
    ? attachment.url
    : (attachment.thumbnail_url ?? attachment.url)
}
</script>

<template>
  <article
    :id="`post-${post.post_number}`"
    class="border border-border rounded p-4"
    :class="{ 'bg-surface': post.is_op }"
  >
    <div class="flex items-center justify-between gap-2 mb-2">
      <div class="flex flex-wrap items-baseline gap-x-2 gap-y-1 text-sm">
        <span class="font-semibold text-accent">{{ post.name }}</span>
        <span v-if="post.tripcode" class="font-mono text-secondary">{{ post.tripcode }}</span>
        <span class="text-secondary">{{ formatDate(post.created_at) }}</span>
        <span class="font-mono text-secondary">No.{{ post.post_number }}</span>
        <span v-if="post.is_edited" class="text-xs text-secondary italic">(edited)</span>
        <span v-if="post.sage" class="text-xs text-secondary">sage</span>
      </div>

      <BaseButton
        v-if="post.is_edited && !isEditing"
        variant="ghost"
        size="sm"
        class="shrink-0"
        @mouseenter="showOriginal = true"
        @mouseleave="showOriginal = false"
      >
        <span class="inline-block w-28 text-right">{{ showOriginal ? 'original' : 'show original' }}</span>
      </BaseButton>
    </div>

    <div
      v-if="post.attachments && post.attachments.length"
      class="flex flex-wrap gap-3 mb-3"
    >
      <template v-for="att in post.attachments" :key="att.id">
        <video
          v-if="isVideo(att)"
          :src="att.url"
          :title="`${att.original_name} (${formatSize(att.size_bytes)})`"
          controls
          preload="metadata"
          class="max-h-64 max-w-full rounded border border-border"
        />
        <a v-else :href="att.url" target="_blank" rel="noopener" class="block cursor-pointer">
          <img
            v-if="isImage(att)"
            :src="imageSrc(att)"
            :alt="att.original_name"
            :title="`${att.original_name} (${formatSize(att.size_bytes)})`"
            class="max-h-32 max-w-32 object-contain rounded border border-border"
          />
          <div
            v-else
            class="flex items-center gap-1 text-xs text-accent hover:underline"
          >
            📎 {{ att.original_name }}
          </div>
        </a>
      </template>
    </div>

    <div v-if="isEditing" class="flex flex-col gap-2">
      <MarkupTextarea v-model="editDraft" rows="4" maxlength="5000" />
      <p v-if="editError" class="text-sm text-red-500">{{ editError }}</p>
      <div class="flex gap-2">
        <BaseButton variant="primary" size="sm" :disabled="isSaving" @click="saveEdit">
          {{ isSaving ? 'Saving…' : 'Edit' }}
        </BaseButton>
        <BaseButton variant="ghost" size="sm" :disabled="isSaving" @click="cancelEdit">Cancel</BaseButton>
      </div>
    </div>

    <template v-else>
      <!-- body: server-rendered html (backlinks/greentext) styled via scoped css -->
      <div
        v-if="bodyHtml"
        class="prose prose-sm post-body"
        v-html="bodyHtml"
      />
      <div v-else-if="post.body" class="text-sm whitespace-pre-wrap">{{ post.body }}</div>

      <div
        v-if="showOriginal && original"
        class="mt-2 border-l-2 border-border pl-2 text-sm text-secondary"
      >
        <div v-if="originalBodyHtml" class="prose prose-sm post-body" v-html="originalBodyHtml" />
        <div v-else-if="original.original_body" class="whitespace-pre-wrap">{{ original.original_body }}</div>
        <div v-else class="italic">(empty)</div>
      </div>

      <div v-if="post.can_edit" class="mt-2 flex justify-end">
        <BaseButton variant="ghost" size="sm" @click="startEdit">Edit</BaseButton>
      </div>
    </template>

    <div v-if="auth.isAuthenticated" class="mt-3 flex flex-col gap-2 border-t border-border pt-2">
      <div class="flex gap-2">
        <BaseButton variant="danger" size="sm" @click="onDelete">Delete</BaseButton>
        <BaseButton variant="ghost" size="sm" @click="startBan">Ban</BaseButton>
      </div>
      <div v-if="isBanning" class="flex items-center gap-2">
        <BaseInput v-model="banReason" placeholder="Ban reason (optional)" />
        <BaseButton variant="danger" size="sm" @click="confirmBan">Confirm ban</BaseButton>
        <BaseButton variant="ghost" size="sm" @click="cancelBan">Cancel</BaseButton>
      </div>
    </div>
  </article>
</template>

<style scoped>
.post-body :deep(blockquote),
.post-body :deep(.greentext) {
  color: var(--color-greentext, #789922);
}

.post-body :deep(a.post-ref) {
  color: var(--color-accent);
  cursor: pointer;
}

.post-body :deep(a.post-ref:hover) {
  text-decoration: underline;
}

/* spoiler: solid box until hovered; children inherit the revealed colour so
   nested markup (links, code) stays hidden too */
.post-body :deep(.spoiler),
.post-body :deep(.spoiler *) {
  background: var(--color-text);
  color: transparent;
}

.post-body :deep(.spoiler) {
  border-radius: 2px;
}

.post-body :deep(.spoiler:hover) {
  color: var(--color-surface);
}

.post-body :deep(.spoiler:hover *) {
  color: inherit;
}

.post-body :deep(code) {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 2px;
  padding: 0 0.25em;
}

.post-body :deep(pre) {
  counter-reset: code-line;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  padding: 0.5rem 0.75rem;
  margin: 0.25rem 0;
  overflow-x: auto;
  line-height: 1.5;
}

.post-body :deep(pre code) {
  background: transparent;
  border: none;
  border-radius: 0;
  padding: 0;
  display: block;
}

.post-body :deep(.code-line) {
  display: block;
  counter-increment: code-line;
  position: relative;
  padding-left: 2.5rem;
  min-height: 1.5em;
}

.post-body :deep(.code-line)::before {
  content: counter(code-line);
  position: absolute;
  left: 0;
  width: 1.75rem;
  text-align: right;
  color: var(--color-text-muted);
  user-select: none;
}
</style>
