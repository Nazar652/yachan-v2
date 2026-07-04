import { apiClient } from '@/api/client'
import { toApiError } from '@/api/errors'

// public report endpoint. the backend always answers 204: a duplicate or
// rate-capped report is dropped silently, so the caller can't tell whether
// a row was actually written — by design.
export async function createReport(
  boardSlug: string,
  postNumber: number,
  reason: string | null,
): Promise<void> {
  const { error, response } = await apiClient.POST(
    '/api/{board_slug}/posts/{post_number}/report',
    {
      params: { path: { board_slug: boardSlug, post_number: postNumber } },
      body: { reason },
    },
  )
  if (error) throw toApiError(error, response)
}
