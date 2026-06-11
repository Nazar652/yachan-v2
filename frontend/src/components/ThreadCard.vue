<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

import BaseButton from '@/components/ui/BaseButton.vue'
import PostBody from '@/components/ui/PostBody.vue'
import { formatDateTime } from '@/utils/display'
import type { ImagePreview, ThreadResponse } from '@/api/types'

// catalog thread card, "variant D": single image -> image + op text in the
// left column, latest replies on the right; several images -> gallery across
// the top, then text left / replies right
const props = defineProps<{
  thread: ThreadResponse
  slug: string
  isMod: boolean
}>()

const emit = defineEmits<{
  'toggle-lock': []
  'toggle-sticky': []
}>()

const router = useRouter()
const threadTo = computed(() => `/${props.slug}/thread/${props.thread.id}`)

function openThread() {
  router.push(threadTo.value)
}

function replyTo(replyPostNumber: number): string {
  return `${threadTo.value}#post-${replyPostNumber}`
}
const images = computed(() => props.thread.op_post?.images ?? [])
const isSingleImage = computed(() => images.value.length <= 1)
const lastReplies = computed(() => props.thread.last_replies ?? [])

const LONG_TEXT_THRESHOLD = 320
const isLongText = computed(
  () => (props.thread.op_post?.body?.length ?? 0) > LONG_TEXT_THRESHOLD,
)

// thumbnails keep the image's own aspect ratio; only ratios beyond 1:4 are
// clamped, so object-cover crops nothing but the extreme cases
const MAX_ASPECT_RATIO = 4
const SINGLE_MAX_WIDTH = 340
const SINGLE_MAX_HEIGHT = 260
const GALLERY_HEIGHT = 114

function clampedRatio(image: ImagePreview): number | null {
  if (!image.width || !image.height) return null
  return Math.min(Math.max(image.width / image.height, 1 / MAX_ASPECT_RATIO), MAX_ASPECT_RATIO)
}

function singleImageStyle(image: ImagePreview): { width: string; height: string } {
  const ratio = clampedRatio(image)
  if (ratio === null) return { width: '200px', height: '200px' }
  let width = SINGLE_MAX_WIDTH
  let height = width / ratio
  if (height > SINGLE_MAX_HEIGHT) {
    height = SINGLE_MAX_HEIGHT
    width = height * ratio
  }
  return { width: `${Math.round(width)}px`, height: `${Math.round(height)}px` }
}

function galleryImageStyle(image: ImagePreview): { width: string; height: string } {
  const ratio = clampedRatio(image)
  if (ratio === null) return { width: '148px', height: `${GALLERY_HEIGHT}px` }
  return { width: `${Math.round(GALLERY_HEIGHT * ratio)}px`, height: `${GALLERY_HEIGHT}px` }
}
</script>

<template>
  <article
    class="flex cursor-pointer flex-col rounded-card border border-border bg-surface shadow-card transition-colors hover:border-gold hover:bg-[color-mix(in_srgb,var(--color-gold)_6%,var(--color-surface))]"
    @click="openThread"
  >
    <div class="flex flex-col gap-3.5 p-5">
      <!-- head -->
      <div class="flex flex-wrap items-baseline gap-2.5">
        <span class="font-mono text-xs text-text-muted">No.{{ thread.id }}</span>
        <RouterLink
          :to="threadTo"
          class="font-display text-[19px] font-extrabold tracking-tight transition-colors hover:text-accent"
          :class="thread.title ? 'text-text' : 'font-normal text-text-muted'"
        >
          {{ thread.title ?? '(no title)' }}
        </RouterLink>
        <span
          v-if="thread.is_sticky"
          class="rounded-full bg-gold/25 px-2 py-0.5 font-mono text-[10.5px] font-semibold uppercase tracking-wide text-accent"
        >
          ★ sticky
        </span>
        <span
          v-if="thread.is_locked"
          class="rounded-full bg-danger/15 px-2 py-0.5 font-mono text-[10.5px] font-semibold uppercase tracking-wide text-danger"
        >
          ⊘ locked
        </span>
        <span class="ml-auto font-mono text-xs text-text-muted">
          {{ thread.reply_count }} {{ thread.reply_count === 1 ? 'reply' : 'replies' }}
          <template v-if="images.length"> · {{ images.length }} img</template>
        </span>
      </div>

      <!-- several images: gallery across the top -->
      <div v-if="!isSingleImage" class="gallery-scroll flex gap-2 overflow-x-auto pb-1.5">
        <RouterLink v-for="(image, index) in images" :key="index" :to="threadTo" class="shrink-0">
          <img
            :src="image.thumbnail_url"
            :style="galleryImageStyle(image)"
            alt=""
            loading="lazy"
            class="rounded-field bg-surface-2 object-cover"
          />
        </RouterLink>
      </div>

      <!-- lower split: op text left, latest replies right -->
      <div class="grid items-start gap-6 md:grid-cols-[1fr_288px]">
        <div class="min-w-0">
          <RouterLink v-if="isSingleImage && images[0]" :to="threadTo" class="mb-3 inline-block">
            <img
              :src="images[0].thumbnail_url"
              :style="singleImageStyle(images[0])"
              alt=""
              loading="lazy"
              class="max-w-full rounded-field bg-surface-2 object-cover"
            />
          </RouterLink>
          <template v-if="thread.op_post?.body_html">
            <PostBody
              :html="thread.op_post.body_html"
              class="text-[14.5px] leading-relaxed"
              :class="{ 'line-clamp-[7] overflow-hidden': isLongText }"
            />
            <RouterLink
              v-if="isLongText"
              :to="threadTo"
              class="mt-1.5 inline-block font-mono text-xs text-accent hover:underline"
            >
              Read more →
            </RouterLink>
          </template>
          <p v-else class="text-sm italic text-text-muted">No text.</p>
        </div>

        <div class="flex min-w-0 flex-col gap-1.5">
          <p
            v-if="lastReplies.length"
            class="font-mono text-[10px] uppercase tracking-[0.12em] text-text-muted"
          >
            Latest {{ lastReplies.length }} {{ lastReplies.length === 1 ? 'reply' : 'replies' }}
          </p>
          <p v-else class="text-[12.5px] italic text-text-muted">
            Nobody posted anything yet — be the first to sow.
          </p>
          <RouterLink
            v-for="reply in lastReplies"
            :key="reply.id"
            :to="replyTo(reply.post_number)"
            class="min-w-0 rounded-field border border-border-soft bg-surface-2 px-2.5 py-1.5 transition-colors hover:border-gold"
            @click.stop
          >
            <div class="flex justify-between font-mono text-[11px] text-text-muted">
              <span class="text-accent">No.{{ reply.post_number }}</span>
              <span>{{ formatDateTime(reply.created_at) }}</span>
            </div>
            <PostBody
              v-if="reply.body_html"
              :html="reply.body_html"
              class="line-clamp-2 overflow-hidden text-[12.5px]"
            />
          </RouterLink>
        </div>
      </div>
    </div>

    <!-- mod controls outside the link targets -->
    <div
      v-if="isMod"
      class="flex gap-3.5 rounded-b-card border-t border-border bg-[color-mix(in_srgb,var(--color-gold)_7%,var(--color-surface))] px-5 py-2"
      @click.stop
    >
      <BaseButton variant="ghost" size="sm" @click="emit('toggle-lock')">
        {{ thread.is_locked ? 'Unlock' : 'Lock' }}
      </BaseButton>
      <BaseButton variant="ghost" size="sm" @click="emit('toggle-sticky')">
        {{ thread.is_sticky ? 'Unsticky' : 'Sticky' }}
      </BaseButton>
    </div>
  </article>
</template>
