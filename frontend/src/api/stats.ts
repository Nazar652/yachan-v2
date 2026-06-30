import { apiClient } from '@/api/client'
import { toApiError } from '@/api/errors'
import type { SiteStatsResponse } from '@/api/types'

export async function fetchSiteStats(): Promise<SiteStatsResponse> {
  const { data, error, response } = await apiClient.GET('/api/stats')
  if (error) throw toApiError(error, response)
  return data
}
