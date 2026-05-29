import { apiClient } from '@/api/client'
import type { BoardResponse } from '@/api/types'

// thin typed wrappers over the boards endpoints. openapi-fetch returns
// { data, error }; we throw on error so tanstack query owns the loading,
// error and retry state instead of every caller unpacking the result.
export async function listBoards(): Promise<BoardResponse[]> {
  const { data, error } = await apiClient.GET('/api/boards')
  if (error) throw error
  return data
}
