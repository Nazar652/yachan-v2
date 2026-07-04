import { apiClient } from '@/api/client'
import { toApiError } from '@/api/errors'
import type { BoardResponse } from '@/api/types'

// thin typed wrappers over the boards endpoints. openapi-fetch returns
// { data, error }; we throw on error so tanstack query owns the loading,
// error and retry state instead of every caller unpacking the result.
export async function listBoards(): Promise<BoardResponse[]> {
  const { data, error, response } = await apiClient.GET('/api/boards')
  if (error) throw toApiError(error, response)
  return data
}

export async function getBoard(slug: string): Promise<BoardResponse> {
  const { data, error, response } = await apiClient.GET('/api/boards/{slug}', {
    params: { path: { slug } },
  })
  if (error) throw toApiError(error, response)
  return data
}
