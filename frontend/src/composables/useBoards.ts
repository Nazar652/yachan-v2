import { useQuery } from '@tanstack/vue-query'

import { listBoards } from '@/api/boards'

// query keys live next to the composable so cache invalidation elsewhere
// (e.g. after a board is created) references one canonical key.
export const boardsQueryKey = ['boards'] as const

export function useBoards() {
  return useQuery({
    queryKey: boardsQueryKey,
    queryFn: listBoards,
  })
}
