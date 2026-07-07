<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'

import PostBody from '@/components/ui/PostBody.vue'
import type { ThreadResponse } from '@/api/types'

// catalog gallery tile: a thumbnail with title/counters, plus a fixed-height
// chunk of the formatted op text so every tile is the same height regardless
// of how much the op wrote. read-only view mode - no mod actions here, list
// mode stays the place for moderation.
const props = defineProps<{
  thread: ThreadResponse
  slug: string
}>()

const threadTo = computed(() => `/${props.slug}/thread/${props.thread.id}`)
const thumbnailUrl = computed(() => props.thread.op_post?.thumbnail_url ?? null)
const imageCount = computed(() => props.thread.op_post?.images?.length ?? 0)

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
    class="flex h-full flex-col overflow-hidden rounded-card border border-border bg-surface shadow-card transition-colors hover:border-gold"
  >
    <div class="relative aspect-[4/3] w-full shrink-0 bg-surface-2">
      <img
        v-if="thumbnailUrl"
        :src="thumbnailUrl"
        alt=""
        loading="lazy"
        class="h-full w-full object-cover"
      />
      <div v-else class="flex h-full w-full items-center justify-center">
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
    </div>

    <div class="flex min-w-0 flex-1 flex-col gap-1 p-2.5">
      <div class="flex items-center justify-between gap-1.5">
        <span class="min-w-0 truncate font-mono text-[11px] font-semibold text-text">{{
          displayTitle
        }}</span>
        <span class="shrink-0 font-mono text-[10.5px] text-text-muted"
          >R: {{ thread.reply_count }} / I: {{ imageCount }}</span
        >
      </div>

      <div class="h-[104px] overflow-hidden">
        <PostBody
          v-if="thread.op_post?.body_html"
          :html="thread.op_post.body_html"
          class="line-clamp-5 overflow-hidden text-[12px] leading-relaxed"
        />
        <p v-else class="text-[11.5px] italic text-text-muted">No text.</p>
      </div>
    </div>
  </RouterLink>
</template>
