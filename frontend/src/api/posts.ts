import { apiClient } from '@/api/client'
import type { PostEditResponse, PostResponse } from '@/api/types'

export async function editPost(
  boardSlug: string,
  postNumber: number,
  newBody: string | null,
): Promise<PostResponse> {
  const { data, error } = await apiClient.PATCH('/api/{board_slug}/posts/{post_number}', {
    params: { path: { board_slug: boardSlug, post_number: postNumber } },
    body: { new_body: newBody },
  })
  if (error) throw error
  return data
}

export async function getPostHistory(
  boardSlug: string,
  postNumber: number,
): Promise<PostEditResponse | null> {
  const { data, error } = await apiClient.GET('/api/{board_slug}/posts/{post_number}/history', {
    params: { path: { board_slug: boardSlug, post_number: postNumber } },
  })
  if (error) throw error
  return data ?? null
}
