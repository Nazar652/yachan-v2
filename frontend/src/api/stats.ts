import { apiClient } from '@/api/client'
import type { SiteStatsResponse } from '@/api/types'

export async function fetchSiteStats(): Promise<SiteStatsResponse> {
  const { data, error } = await apiClient.GET('/api/stats')
  if (error) throw error
  return data
}
