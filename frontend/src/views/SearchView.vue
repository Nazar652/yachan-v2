<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import { useSearch } from '@/composables/useSearch'
import { formatCompactWhen } from '@/utils/display'

const route = useRoute()
const router = useRouter()

const queryText = computed(() => (typeof route.query.q === 'string' ? route.query.q : ''))
const board = computed(() => (typeof route.query.board === 'string' ? route.query.board : null))

const term = ref(queryText.value)
watch(queryText, (value) => {
  term.value = value
})

function submit() {
  const trimmed = term.value.trim()
  router.replace({
    name: 'search',
    query: trimmed ? { q: trimmed, ...(board.value ? { board: board.value } : {}) } : {},
  })
}

const { data: results, isFetching, isError } = useSearch(queryText, board)

const hasQuery = computed(() => queryText.value.trim().length >= 2)
</script>

<template>
  <section class="pt-3 pb-2">
    <div class="mb-5 flex items-center gap-3">
      <h1 class="font-display text-[22px] font-extrabold">Search</h1>
      <span class="h-px flex-1 bg-border" />
    </div>

    <form class="mb-6 flex gap-2" @submit.prevent="submit">
      <input
        v-model="term"
        type="search"
        placeholder="Search posts…"
        aria-label="Search posts"
        class="w-full rounded-field border border-border bg-bg px-3 py-2 text-sm text-text outline-none transition-colors placeholder:text-text-muted focus:border-gold focus:ring-[3px] focus:ring-gold/25"
      />
      <button
        type="submit"
        class="shrink-0 cursor-pointer rounded-field bg-gold px-4 py-2 text-sm font-semibold text-on-gold shadow-card transition-colors hover:bg-gold-2"
      >
        Search
      </button>
    </form>

    <p v-if="!hasQuery" class="text-text-muted">Type at least two characters to search.</p>
    <p v-else-if="isFetching && !results" class="text-text-muted">Searching…</p>
    <p v-else-if="isError" class="text-danger">Search failed. Try again.</p>
    <p v-else-if="!results?.length" class="text-text-muted">
      No posts match “{{ queryText }}”.
    </p>

    <ul v-else class="flex flex-col gap-2.5">
      <li v-for="result in results" :key="`${result.board_slug}-${result.post_number}`">
        <RouterLink
          :to="`/${result.board_slug}/thread/${result.thread_id}#post-${result.post_number}`"
          class="flex flex-col gap-1.5 rounded-card border border-border bg-surface px-4 py-3 shadow-card transition-all hover:translate-x-0.5 hover:border-gold"
        >
          <div class="flex items-center gap-2 font-mono text-[11px] text-text-muted">
            <span class="rounded-full bg-gold px-2 py-0.5 font-semibold text-on-gold">
              /{{ result.board_slug }}/
            </span>
            <span>No.{{ result.post_number }}</span>
            <span v-if="result.is_op" class="font-semibold text-greentext">OP</span>
            <span class="ml-auto">{{ formatCompactWhen(result.created_at) }}</span>
          </div>
          <p class="line-clamp-3 whitespace-pre-wrap text-[13.5px] text-text">
            {{ result.body || '(no text)' }}
          </p>
        </RouterLink>
      </li>
    </ul>
  </section>
</template>
