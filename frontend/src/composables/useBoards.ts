import { computed, toValue, type MaybeRefOrGetter } from 'vue'
import { useQuery } from '@tanstack/vue-query'

import { getBoard, listBoards } from '@/api/boards'

// query keys live next to the composable so cache invalidation elsewhere
// (e.g. after a board is created) references one canonical key. the per-slug
// key extends the list key, so invalidating the prefix refreshes both.
export const boardsQueryKey = ['boards'] as const

export function boardQueryKey(slug: string) {
  return [...boardsQueryKey, slug] as const
}

export function useBoards() {
  return useQuery({
    queryKey: boardsQueryKey,
    queryFn: listBoards,
  })
}

export function useBoard(slug: MaybeRefOrGetter<string>) {
  return useQuery({
    queryKey: computed(() => boardQueryKey(toValue(slug))),
    queryFn: () => getBoard(toValue(slug)),
  })
}
