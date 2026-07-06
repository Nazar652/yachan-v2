<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter, RouterLink, type LocationQueryValue } from 'vue-router'

import { useBoard } from '@/composables/useBoards'
import { useThreads, THREADS_PAGE_SIZE } from '@/composables/useThreads'
import { useSiteStats } from '@/composables/useSiteStats'
import { useBoardWs } from '@/composables/useBoardWs'
import { useCatalogModeration } from '@/composables/useCatalogModeration'
import { useAuthStore } from '@/stores/auth'
import BaseButton from '@/components/ui/BaseButton.vue'
import CatalogPager from '@/components/ui/CatalogPager.vue'
import ThreadCard from '@/components/ThreadCard.vue'
import type { ThreadResponse } from '@/api/types'

const route = useRoute()
const router = useRouter()
const slug = computed(() => route.params.slug as string)

function firstQueryValue(value: LocationQueryValue | LocationQueryValue[] | undefined) {
  return Array.isArray(value) ? value[0] : value
}

const page = computed(() => {
  const parsed = Number(firstQueryValue(route.query.page))
  return Number.isInteger(parsed) && parsed >= 1 ? parsed : 1
})

type SortKey = 'bump' | 'new' | 'replies'
const SORT_KEYS: SortKey[] = ['bump', 'new', 'replies']
const sort = computed<SortKey>(() => {
  const raw = firstQueryValue(route.query.sort)
  return (SORT_KEYS as string[]).includes(raw ?? '') ? (raw as SortKey) : 'bump'
})

const { data: board } = useBoard(slug)
const { data: stats } = useSiteStats()
const { data: threads, isPending, isError } = useThreads(slug, page)

useBoardWs(slug)

const auth = useAuthStore()
const moderation = useCatalogModeration(slug, page)

const boardStats = computed(() =>
  stats.value?.boards.find((candidate) => candidate.slug === slug.value),
)
const totalPages = computed(() =>
  boardStats.value ? Math.max(1, Math.ceil(boardStats.value.thread_count / THREADS_PAGE_SIZE)) : 1,
)

const sortOptions: Array<[SortKey, string]> = [
  ['bump', 'Bump order'],
  ['new', 'Newest'],
  ['replies', 'Most replies'],
]

// the server returns bump order (sticky first); the other keys reorder the page
const sortedThreads = computed(() => {
  const list = threads.value ?? []
  if (sort.value === 'new') {
    return [...list].sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
    )
  }
  if (sort.value === 'replies') {
    return [...list].sort((a, b) => b.reply_count - a.reply_count)
  }
  return list
})

function setPage(nextPage: number) {
  const query = { ...route.query, page: nextPage === 1 ? undefined : String(nextPage) }
  router.replace({ query })
  window.scrollTo({ top: 0 })
}

function setSort(nextSort: SortKey) {
  const query = { ...route.query, sort: nextSort === 'bump' ? undefined : nextSort }
  router.replace({ query })
}

async function onToggleLock(thread: ThreadResponse) {
  await moderation.setLocked(thread.id, !thread.is_locked)
}

async function onToggleSticky(thread: ThreadResponse) {
  await moderation.setSticky(thread.id, !thread.is_sticky)
}
</script>

<template>
  <section class="pt-2">
    <div
      class="flex flex-col gap-3 rounded-card border border-border border-l-4 border-l-gold bg-surface px-5 py-4 shadow-card sm:flex-row sm:items-center sm:gap-4"
    >
      <div class="flex min-w-0 items-center gap-4">
        <span class="font-mono text-[26px] font-bold text-gold-2">/{{ slug }}/</span>
        <div class="min-w-0">
          <div v-if="board" class="flex items-center gap-2">
            <span class="font-display text-lg font-bold">{{ board.title }}</span>
            <span
              v-if="board.is_nsfw"
              class="rounded bg-danger/10 px-1.5 py-0.5 font-mono text-[10px] font-bold text-danger"
              >18+</span
            >
          </div>
          <div v-if="board?.description" class="text-[15px] text-text-muted">
            {{ board.description }}
          </div>
        </div>
      </div>
      <div
        v-if="boardStats"
        class="shrink-0 font-mono text-xs text-text-muted sm:ml-auto sm:text-right"
      >
        <div>
          <b class="text-text">{{ boardStats.thread_count }}</b> threads ·
          <b class="text-text">{{ boardStats.post_count }}</b> posts
        </div>
        <div class="text-greentext">● {{ boardStats.online_count }} online now</div>
      </div>
    </div>

    <div class="my-4 flex flex-col-reverse gap-3 sm:flex-row sm:items-center">
      <div class="flex w-full overflow-hidden rounded-field border border-border sm:inline-flex sm:w-auto">
        <button
          v-for="[key, label] in sortOptions"
          :key="key"
          type="button"
          class="flex-1 cursor-pointer border-border px-3 py-1.5 font-mono text-xs transition-colors not-first:border-l sm:flex-none"
          :class="
            sort === key
              ? 'bg-gold font-bold text-on-gold'
              : 'bg-surface text-text-muted hover:bg-surface-3'
          "
          @click="setSort(key)"
        >
          {{ label }}
        </button>
      </div>
      <div class="hidden flex-1 sm:block" />
      <RouterLink :to="`/${slug}/new`" class="block w-full sm:w-auto">
        <BaseButton variant="primary" class="w-full sm:w-auto">+ New thread</BaseButton>
      </RouterLink>
    </div>

    <p v-if="isPending" class="mt-2 text-text-muted">Loading…</p>
    <p v-else-if="isError" class="mt-2 text-danger">Failed to load threads.</p>
    <p v-else-if="!threads?.length" class="mt-4 text-text-muted">No threads yet.</p>

    <ul v-else class="flex flex-col gap-2.5">
      <li v-for="thread in sortedThreads" :key="thread.id">
        <ThreadCard
          :thread="thread"
          :slug="slug"
          :is-mod="auth.isAuthenticated"
          @toggle-lock="onToggleLock(thread)"
          @toggle-sticky="onToggleSticky(thread)"
        />
      </li>
    </ul>

    <CatalogPager :page="page" :total="totalPages" @update:page="setPage" />
  </section>
</template>
