import { computed, toValue, type MaybeRefOrGetter } from 'vue'
import { useQuery } from '@tanstack/vue-query'

import { listThreads } from '@/api/threads'

export const threadsQueryKey = (slug: string) => ['threads', slug] as const

export function useThreads(slug: MaybeRefOrGetter<string>) {
  return useQuery({
    queryKey: computed(() => threadsQueryKey(toValue(slug))),
    queryFn: () => listThreads(toValue(slug)),
  })
}

