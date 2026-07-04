import { computed, toValue, type MaybeRefOrGetter } from 'vue'
import { useQuery } from '@tanstack/vue-query'

import { listReports } from '@/api/mod'

// query key lives next to the composable so the dashboard can invalidate it
// after resolving a report. the board filter extends the key, so invalidating
// the bare prefix refreshes every filtered variant too.
export const reportsQueryKey = ['reports'] as const

export function useReports(boardId: MaybeRefOrGetter<number | null> = null) {
  return useQuery({
    queryKey: computed(() => [...reportsQueryKey, toValue(boardId)] as const),
    queryFn: () => listReports(toValue(boardId)),
  })
}
