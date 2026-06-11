import { useQuery } from '@tanstack/vue-query'

import { listLatestThreads } from '@/api/threads'

export const latestThreadsQueryKey = ['latest-threads'] as const

export function useLatestThreads() {
  return useQuery({
    queryKey: latestThreadsQueryKey,
    queryFn: () => listLatestThreads(),
  })
}
