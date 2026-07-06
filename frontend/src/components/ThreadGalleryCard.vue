<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'

import type { ThreadResponse } from '@/api/types'

// catalog gallery tile: a square thumbnail with title/reply-count overlaid at
// the bottom and lock/sticky badges in the corner. no mod actions here — this
// is a read-only view mode, list mode stays the place for moderation.
const props = defineProps<{
  thread: ThreadResponse
  slug: string
}>()

const threadTo = computed(() => `/${props.slug}/thread/${props.thread.id}`)
const thumbnailUrl = computed(() => props.thread.op_post?.thumbnail_url ?? null)

const TITLE_FALLBACK_LENGTH = 60
const displayTitle = computed(() => {
  if (props.thread.title) return props.thread.title
  const body = props.thread.op_post?.body
  if (!body) return '(no title)'
  return body.length > TITLE_FALLBACK_LENGTH ? `${body.slice(0, TITLE_FALLBACK_LENGTH)}…` : body
})
</script>

<template>
  <RouterLink
    :to="threadTo"
    class="group relative block aspect-square overflow-hidden rounded-card border border-border bg-surface shadow-card transition-colors hover:border-gold"
  >
    <img
      v-if="thumbnailUrl"
      :src="thumbnailUrl"
      alt=""
      loading="lazy"
      class="h-full w-full object-cover"
    />
    <div v-else class="flex h-full w-full items-center justify-center bg-surface-2">
      <span class="text-[11px] italic text-text-muted">no image</span>
    </div>

    <div class="absolute top-1.5 right-1.5 flex gap-1">
      <span
        v-if="thread.is_sticky"
        title="Sticky"
        class="flex h-5 w-5 items-center justify-center rounded-full bg-surface/85 text-[11px]"
        >📌</span
      >
      <span
        v-if="thread.is_locked"
        title="Locked"
        class="flex h-5 w-5 items-center justify-center rounded-full bg-surface/85 text-[11px]"
        >🔒</span
      >
    </div>

    <div
      class="absolute inset-x-0 bottom-0 flex items-center justify-between gap-1.5 bg-surface/90 px-1.5 py-1"
    >
      <span class="min-w-0 truncate font-mono text-[11px] font-semibold text-text">{{
        displayTitle
      }}</span>
      <span class="shrink-0 font-mono text-[10.5px] text-text-muted">R: {{ thread.reply_count }}</span>
    </div>
  </RouterLink>
</template>
