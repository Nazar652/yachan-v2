import { apiClient } from '@/api/client'
import { toApiError } from '@/api/errors'
import type { SearchResultResponse, SimilarThreadResponse } from '@/api/types'

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

export async function getSimilarThreads(
  boardSlug: string,
  threadId: number,
): Promise<SimilarThreadResponse[]> {
  const { data, error, response } = await apiClient.GET(
    '/api/{board_slug}/threads/{thread_id}/similar',
    { params: { path: { board_slug: boardSlug, thread_id: threadId } } },
  )
  if (error) throw toApiError(error, response)
  return data
}

export async function getSimilarThreadsForText(
  boardSlug: string,
  q: string,
): Promise<SimilarThreadResponse[]> {
  const { data, error, response } = await apiClient.GET('/api/{board_slug}/threads/similar', {
    params: { path: { board_slug: boardSlug }, query: { q } },
  })
  if (error) throw toApiError(error, response)
  return data
}
