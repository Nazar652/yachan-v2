import { computed, toValue, type MaybeRefOrGetter } from 'vue'
import { keepPreviousData, useQuery } from '@tanstack/vue-query'

import { listThreads } from '@/api/threads'

export const THREADS_PAGE_SIZE = 10

// prefix key — invalidating it touches every cached page of the board
export const threadsQueryKey = (slug: string) => ['threads', slug] as const

export const threadsPageQueryKey = (slug: string, page: number) =>
  ['threads', slug, page] as const

export function useThreads(slug: MaybeRefOrGetter<string>, page: MaybeRefOrGetter<number> = 1) {
  return useQuery({
    queryKey: computed(() => threadsPageQueryKey(toValue(slug), toValue(page))),
    queryFn: () =>
      listThreads(toValue(slug), THREADS_PAGE_SIZE, (toValue(page) - 1) * THREADS_PAGE_SIZE),
    // keep showing the previous page while the next one loads
    placeholderData: keepPreviousData,
  })
}
