<script setup lang="ts">
import { ref, toRef } from 'vue'

import { useModeration } from '@/composables/useModeration'
import { useEditPost } from '@/composables/useEditPost'
import { useOwnPosts } from '@/composables/useOwnPosts'
import { usePostHistory } from '@/composables/usePostHistory'
import { useAuthStore } from '@/stores/auth'
import { errorDetail } from '@/api/errors'
import type { AttachmentResponse, PostResponse } from '@/api/types'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseInput from '@/components/ui/BaseInput.vue'
import MarkupTextarea from '@/components/ui/MarkupTextarea.vue'
import PostBody from '@/components/ui/PostBody.vue'

const props = withDefaults(
  defineProps<{
    post: PostResponse
    slug: string
    threadId: number
    backlinks?: number[]
  }>(),
  { backlinks: () => [] },
)

const emit = defineEmits<{
  quote: [postNumber: number]
  navigate: [postNumber: number]
}>()

const auth = useAuthStore()
const { isOwn, ownNumbers } = useOwnPosts(() => props.slug)
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
    editError.value = errorDetail(error, 'Failed to edit post.')
  } finally {
    isSaving.value = false
  }
}

// show-original: fetch the pre-edit body lazily and only while the button is hovered
const showOriginal = ref(false)
const { data: original } = usePostHistory(toRef(props, 'slug'), props.post.post_number, showOriginal)

const isBanning = ref(false)
const banReason = ref('')
const modError = ref<string | null>(null)

async function onDelete() {
  modError.value = null
  try {
    await moderation.removePost(props.post.post_number)
  } catch (error: unknown) {
    modError.value = errorDetail(error, 'Failed to delete post.')
  }
}

function startBan() {
  isBanning.value = true
  banReason.value = ''
  modError.value = null
}

function cancelBan() {
  isBanning.value = false
  banReason.value = ''
}

async function confirmBan() {
  modError.value = null
  try {
    await moderation.ban(props.post.post_number, { reason: banReason.value || null })
    cancelBan()
  } catch (error: unknown) {
    modError.value = errorDetail(error, 'Failed to ban poster.')
  }
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

function imageSrc(attachment: AttachmentResponse): string | undefined {
  const source =
    attachment.media_type === 'gif'
      ? attachment.url
      : (attachment.thumbnail_url ?? attachment.url)
  return source ?? undefined
}

// a hidden attachment comes back from the api with a null url; show why
function isHidden(attachment: AttachmentResponse): boolean {
  return attachment.url === null
}

function hiddenLabel(attachment: AttachmentResponse): string {
  return attachment.moderation_status === 'blocked'
    ? 'Attachment removed by moderation'
    : 'Hidden — 18+ content'
}
</script>

<template>
  <article
    :id="`post-${post.post_number}`"
    class="scroll-mt-20 rounded-card border bg-surface p-4 shadow-card"
    :class="
      post.is_op
        ? 'border-[color-mix(in_srgb,var(--color-gold)_32%,var(--color-border))] bg-surface-2'
        : 'border-border'
    "
  >
    <div class="mb-2 flex items-center justify-between gap-2">
      <div class="flex flex-wrap items-baseline gap-x-2 gap-y-1 text-[13px]">
        <span class="font-bold text-greentext">{{ post.name }}</span>
        <span v-if="post.tripcode" class="font-mono text-text-muted">{{ post.tripcode }}</span>
        <span class="font-mono text-xs text-text-muted">{{ formatDate(post.created_at) }}</span>
        <button
          type="button"
          class="cursor-pointer font-mono text-xs text-text-muted hover:text-accent hover:underline"
          title="Quote this post"
          @click="emit('quote', post.post_number)"
        >
          No.{{ post.post_number }}
        </button>
        <span v-if="isOwn(post.post_number)" class="post-you font-mono text-xs font-bold">(You)</span>
        <span v-if="post.sage" class="text-xs text-text-muted">sage</span>
      </div>

      <div
        v-if="post.is_edited && !isEditing"
        class="edit-wrap relative shrink-0"
        @mouseenter="showOriginal = true"
        @mouseleave="showOriginal = false"
      >
        <span class="edit-chip inline-flex cursor-help items-center gap-1 font-mono text-[11px] text-text-muted">
          <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor"
               stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M3 12a9 9 0 1 0 3-6.7L3 8" /><path d="M3 3v5h5" /><path d="M12 8v4l3 2" />
          </svg>
          edited
        </span>

        <div v-if="showOriginal" class="edit-pop">
          <span class="edit-pop-label">
            Original{{ post.edited_at ? ` · before ${formatDate(post.edited_at)}` : '' }}
          </span>
          <PostBody
            v-if="original && original.original_body_html"
            :html="original.original_body_html"
            :own-numbers="ownNumbers"
            class="text-sm"
            @navigate="emit('navigate', $event)"
          />
          <div v-else-if="original && original.original_body" class="whitespace-pre-wrap text-sm">
            {{ original.original_body }}
          </div>
          <div v-else class="text-sm italic text-text-muted">Loading…</div>
        </div>
      </div>
    </div>

    <div
      v-if="post.attachments && post.attachments.length"
      class="flex flex-wrap gap-3 mb-3"
    >
      <template v-for="att in post.attachments" :key="att.id">
        <div
          v-if="isHidden(att)"
          class="flex h-24 min-w-40 max-w-full items-center justify-center rounded-field border border-dashed border-border bg-surface-2 px-4 text-center text-xs text-text-muted"
        >
          {{ hiddenLabel(att) }}
        </div>
        <video
          v-else-if="isVideo(att)"
          :src="att.url ?? undefined"
          :title="`${att.original_name} (${formatSize(att.size_bytes)})`"
          controls
          preload="metadata"
          class="max-h-64 max-w-full rounded-field border border-border"
        />
        <a v-else :href="att.url ?? undefined" target="_blank" rel="noopener" class="block cursor-pointer">
          <img
            v-if="isImage(att)"
            :src="imageSrc(att)"
            :alt="att.original_name"
            :title="`${att.original_name} (${formatSize(att.size_bytes)})`"
            class="max-h-64 max-w-full rounded-field border border-border object-contain"
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
      <p v-if="editError" class="text-sm text-danger">{{ editError }}</p>
      <div class="flex gap-2">
        <BaseButton variant="primary" size="sm" :disabled="isSaving" @click="saveEdit">
          {{ isSaving ? 'Saving…' : 'Edit' }}
        </BaseButton>
        <BaseButton variant="ghost" size="sm" :disabled="isSaving" @click="cancelEdit">Cancel</BaseButton>
      </div>
    </div>

    <template v-else>
      <PostBody
        v-if="post.body_html"
        :html="post.body_html"
        :own-numbers="ownNumbers"
        class="text-sm"
        @navigate="emit('navigate', $event)"
      />
      <div v-else-if="post.body" class="text-sm whitespace-pre-wrap">{{ post.body }}</div>

      <div v-if="post.can_edit" class="mt-2 flex justify-end">
        <BaseButton variant="ghost" size="sm" @click="startEdit">Edit</BaseButton>
      </div>
    </template>

    <div v-if="backlinks.length" class="post-backlinks mt-2 flex flex-wrap gap-x-2 text-xs">
      <span v-for="backlinkNumber in backlinks" :key="backlinkNumber">
        <a
          class="post-ref"
          :data-post="backlinkNumber"
          @click.prevent="emit('navigate', backlinkNumber)"
        >&gt;&gt;{{ backlinkNumber }}</a>
        <span v-if="isOwn(backlinkNumber)" class="post-you"> (You)</span>
      </span>
    </div>

    <div v-if="auth.isAuthenticated" class="mt-3 flex flex-col gap-2 border-t border-dashed border-border pt-2.5">
      <div class="flex gap-2">
        <BaseButton variant="danger" size="sm" @click="onDelete">Delete</BaseButton>
        <BaseButton variant="ghost" size="sm" @click="startBan">Ban</BaseButton>
      </div>
      <div v-if="isBanning" class="flex items-center gap-2">
        <BaseInput v-model="banReason" placeholder="Ban reason (optional)" />
        <BaseButton variant="danger" size="sm" @click="confirmBan">Confirm ban</BaseButton>
        <BaseButton variant="ghost" size="sm" @click="cancelBan">Cancel</BaseButton>
      </div>
      <p v-if="modError" class="text-sm text-danger">{{ modError }}</p>
    </div>
  </article>
</template>

<style scoped>
.edit-chip {
  border-bottom: 1px dashed color-mix(in srgb, var(--color-text-muted) 60%, transparent);
  padding-bottom: 1px;
  transition: color 0.14s, border-color 0.14s;
}
.edit-wrap:hover .edit-chip {
  color: var(--color-accent);
  border-bottom-color: var(--color-gold);
}

/* original-text popover, drops in below the chip on hover */
.edit-pop {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 8px;
  z-index: 20;
  width: max-content;
  min-width: 200px;
  max-width: 360px;
  text-align: left;
  padding: 10px 13px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-left: 3px solid var(--color-gold);
  border-radius: var(--radius-field);
  box-shadow: var(--shadow-deep);
  animation: edit-pop-in 0.16s ease;
}
/* transparent bridge so the 8px gap doesn't drop the :hover */
.edit-pop::before {
  content: '';
  position: absolute;
  top: -9px;
  left: 0;
  right: 0;
  height: 9px;
}
/* caret pointing up at the chip */
.edit-pop::after {
  content: '';
  position: absolute;
  top: -5px;
  right: 16px;
  width: 9px;
  height: 9px;
  background: var(--color-surface);
  border-left: 1px solid var(--color-border);
  border-top: 1px solid var(--color-border);
  transform: rotate(45deg);
}
.edit-pop-label {
  display: block;
  margin-bottom: 6px;
  font-family: var(--font-mono);
  font-size: 9.5px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--color-accent);
}
@keyframes edit-pop-in {
  from { opacity: 0; transform: translateY(-5px); }
  to   { opacity: 1; transform: translateY(0); }
}
</style>
