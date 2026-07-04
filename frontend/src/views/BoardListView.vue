<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'

import { useBoards } from '@/composables/useBoards'
import { useSiteStats } from '@/composables/useSiteStats'
import { useLatestThreads } from '@/composables/useLatestThreads'
import BarleyEar from '@/components/brand/BarleyEar.vue'
import PostBody from '@/components/ui/PostBody.vue'
import { formatCompactNumber, formatCompactWhen } from '@/utils/display'

const { data: boards, isPending, isError } = useBoards()
const { data: stats } = useSiteStats()
const { data: latest } = useLatestThreads()

const heroStats = computed(() => {
  if (!stats.value) return []
  return [
    [formatCompactNumber(stats.value.board_count), 'boards'],
    [formatCompactNumber(stats.value.thread_count), 'threads'],
    [formatCompactNumber(stats.value.post_count), 'posts'],
    [formatCompactNumber(stats.value.online_count), 'online'],
  ] as Array<[string, string]>
})

const statsBySlug = computed(
  () => new Map((stats.value?.boards ?? []).map((board) => [board.slug, board])),
)
</script>

<template>
  <section class="pt-3 pb-2">
    <div
      class="relative overflow-hidden rounded-hero border border-border p-9 shadow-pop bg-[linear-gradient(180deg,color-mix(in_srgb,var(--color-gold)_16%,var(--color-surface)),var(--color-surface))]"
    >
      <div class="mb-3.5 font-mono text-xs uppercase tracking-[0.22em] text-accent">
        A field for everything
      </div>
      <h1 class="font-display text-5xl font-extrabold leading-[0.98] tracking-tighter">
        The anonymous<br />
        field. <b class="text-gold-2"><span class="text-text">я</span>чан.</b>
      </h1>
      <p class="mt-4 max-w-[56ch] text-base text-text-muted">
        yachan is a small anonymous imageboard. Pick a field below, sow a thread, and let the
        discussion ripen. No accounts, no names required — just bring an image and something to
        say.
      </p>
      <div v-if="heroStats.length" class="mt-6 flex gap-8">
        <div v-for="[value, label] in heroStats" :key="label">
          <div class="font-display text-[26px] font-extrabold text-text">{{ value }}</div>
          <div class="text-xs uppercase tracking-[0.08em] text-text-muted">{{ label }}</div>
        </div>
      </div>
      <div class="pointer-events-none absolute -right-2.5 -bottom-7 opacity-50">
        <BarleyEar :height="210" />
      </div>
    </div>

    <div class="mt-9 mb-4 flex items-center gap-3">
      <h2 class="text-[22px] font-extrabold">Boards</h2>
      <span class="h-px flex-1 bg-border" />
    </div>

    <p v-if="isPending" class="mt-2 text-text-muted">Loading…</p>
    <p v-else-if="isError" class="mt-2 text-danger">Failed to load boards.</p>
    <p v-else-if="!boards?.length" class="mt-2 text-text-muted">No boards yet.</p>

    <ul v-else class="grid grid-cols-1 gap-3.5 sm:grid-cols-2">
      <li v-for="board in boards" :key="board.id">
        <RouterLink
          :to="`/${board.slug}`"
          class="relative flex h-full flex-col overflow-hidden rounded-card border border-border bg-surface p-5 shadow-card transition-all hover:-translate-y-0.5 hover:border-gold hover:shadow-pop after:pointer-events-none after:absolute after:-right-5 after:-top-5 after:h-20 after:w-20 after:content-[''] after:bg-[radial-gradient(circle,color-mix(in_srgb,var(--color-gold)_26%,transparent),transparent_70%)]"
        >
          <div class="flex items-baseline gap-2.5">
            <span class="font-mono font-bold text-gold-2">/{{ board.slug }}/</span>
            <span class="font-display text-lg font-bold text-text">{{ board.title }}</span>
            <span
              v-if="board.is_nsfw"
              class="rounded bg-danger/10 px-1.5 py-0.5 font-mono text-[10px] font-bold text-danger"
              >18+</span
            >
          </div>
          <p v-if="board.description" class="mt-1.5 text-[13.5px] text-text-muted">
            {{ board.description }}
          </p>
          <div
            v-if="statsBySlug.get(board.slug)"
            class="mt-auto flex gap-4 pt-3.5 font-mono text-xs text-text-muted"
          >
            <span><b class="text-text">{{ statsBySlug.get(board.slug)!.thread_count }}</b> threads</span>
            <span><b class="text-text">{{ statsBySlug.get(board.slug)!.post_count }}</b> posts</span>
            <span class="text-greentext">● {{ statsBySlug.get(board.slug)!.online_count }} online</span>
          </div>
        </RouterLink>
      </li>
    </ul>

    <template v-if="latest?.length">
      <div class="mt-9 mb-4 flex items-center gap-3">
        <h2 class="text-[22px] font-extrabold">Latest threads</h2>
        <span class="h-px flex-1 bg-border" />
      </div>
      <ul class="flex flex-col gap-2.5">
        <li v-for="thread in latest" :key="`${thread.board_slug}-${thread.id}`">
          <RouterLink
            :to="`/${thread.board_slug}/thread/${thread.id}`"
            class="flex items-center gap-3.5 rounded-card border border-border bg-surface px-4 py-3 shadow-card transition-all hover:translate-x-0.5 hover:border-gold"
          >
            <img
              v-if="thread.thumbnail_url"
              :src="thread.thumbnail_url"
              alt=""
              loading="lazy"
              class="h-13 w-13 shrink-0 rounded-field bg-surface-2 object-cover"
            />
            <div
              v-else
              class="h-13 w-13 shrink-0 rounded-field bg-surface-2"
              aria-hidden="true"
            />
            <div class="min-w-0 flex-1">
              <div class="text-[14.5px] font-bold text-text">
                {{ thread.title ?? '(no title)' }}
              </div>
              <PostBody
                v-if="thread.last_reply?.body_html"
                :html="thread.last_reply.body_html"
                class="line-clamp-1 overflow-hidden text-[13px] text-text-muted"
              />
              <div
                v-else
                class="overflow-hidden text-ellipsis whitespace-nowrap text-[13px] text-text-muted"
                :class="{ italic: !thread.last_reply }"
              >
                {{ thread.last_reply?.body || 'Nobody posted anything yet' }}
              </div>
            </div>
            <span
              class="shrink-0 rounded-full bg-gold px-2 py-0.5 font-mono text-[11px] font-semibold text-on-gold"
            >
              /{{ thread.board_slug }}/
            </span>
            <span class="shrink-0 font-mono text-[11px] text-text-muted">
              {{ formatCompactWhen(thread.bump_at) }}
            </span>
          </RouterLink>
        </li>
      </ul>
    </template>
  </section>
</template>
