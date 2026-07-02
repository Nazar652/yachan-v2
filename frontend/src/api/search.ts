import { apiClient } from '@/api/client'
import { toApiError } from '@/api/errors'
import type { SearchResultResponse } from '@/api/types'

export async function searchPosts(
  query: string,
  board?: string,
  limit = 20,
): Promise<SearchResultResponse[]> {
  const { data, error, response } = await apiClient.GET('/api/search', {
    params: { query: { q: query, board, limit } },
  })
  if (error) throw toApiError(error, response)
  return data
}
