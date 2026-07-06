import { computed, type Ref } from 'vue'
import { useQuery } from '@tanstack/vue-query'

import { getSimilarThreads } from '@/api/search'

// similarity between threads changes slowly, so keep results fresh for a while
const STALE_TIME_MS = 5 * 60 * 1000

export function similarThreadsQueryKey(slug: string | Ref<string>, threadId: number | Ref<number>) {
  return ['similar-threads', slug, threadId] as const
}

export function useSimilarThreads(slug: Ref<string>, threadId: Ref<number>) {
  return useQuery({
    queryKey: similarThreadsQueryKey(slug, threadId),
    queryFn: () => getSimilarThreads(slug.value, threadId.value),
    enabled: computed(() => Number.isFinite(threadId.value)),
    staleTime: STALE_TIME_MS,
  })
}
