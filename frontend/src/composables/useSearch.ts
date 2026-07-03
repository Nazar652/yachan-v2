import { computed, toValue, type MaybeRefOrGetter } from 'vue'
import { useQuery } from '@tanstack/vue-query'

import { searchPosts } from '@/api/search'

// searches shorter than this are ignored — single characters are just noise
const MIN_QUERY_LENGTH = 2

export function searchQueryKey(query: string, board: string | null) {
  return ['search', query, board] as const
}

export function useSearch(
  query: MaybeRefOrGetter<string>,
  board: MaybeRefOrGetter<string | null>,
) {
  const term = computed(() => toValue(query).trim())
  const boardSlug = computed(() => toValue(board))
  return useQuery({
    queryKey: computed(() => searchQueryKey(term.value, boardSlug.value)),
    queryFn: () => searchPosts(term.value, boardSlug.value ?? undefined),
    enabled: computed(() => term.value.length >= MIN_QUERY_LENGTH),
  })
}
