import { apiClient } from '@/api/client'
import type { ThreadResponse } from '@/api/types'

export async function listThreads(boardSlug: string): Promise<ThreadResponse[]> {
  const { data, error } = await apiClient.GET('/api/{board_slug}/threads', {
    params: { path: { board_slug: boardSlug } },
  })
  if (error) throw error
  return data
}

