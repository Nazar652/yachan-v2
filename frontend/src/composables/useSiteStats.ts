import { useQuery } from '@tanstack/vue-query'

import { fetchSiteStats } from '@/api/stats'

export const siteStatsQueryKey = ['stats'] as const

export function useSiteStats() {
  return useQuery({
    queryKey: siteStatsQueryKey,
    queryFn: fetchSiteStats,
  })
}
