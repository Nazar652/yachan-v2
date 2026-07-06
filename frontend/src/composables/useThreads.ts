import { computed, toValue, type MaybeRefOrGetter } from 'vue'
import { keepPreviousData, useQuery } from '@tanstack/vue-query'

import { listThreads } from '@/api/threads'

export const THREADS_PAGE_SIZE = 10
export const GALLERY_PAGE_SIZE = 40

// prefix key — invalidating it touches every cached page of the board
export const threadsQueryKey = (slug: string) => ['threads', slug] as const

export const threadsPageQueryKey = (slug: string, page: number, pageSize = THREADS_PAGE_SIZE) =>
  ['threads', slug, page, pageSize] as const

export function useThreads(
  slug: MaybeRefOrGetter<string>,
  page: MaybeRefOrGetter<number> = 1,
  pageSize: MaybeRefOrGetter<number> = THREADS_PAGE_SIZE,
) {
  return useQuery({
    queryKey: computed(() =>
      threadsPageQueryKey(toValue(slug), toValue(page), toValue(pageSize)),
    ),
    queryFn: () =>
      listThreads(toValue(slug), toValue(pageSize), (toValue(page) - 1) * toValue(pageSize)),
    // keep showing the previous page while the next one loads
    placeholderData: keepPreviousData,
  })
}
