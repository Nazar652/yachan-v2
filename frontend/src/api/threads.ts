import {apiClient} from '@/api/client'
import type {ThreadDetailResponse, ThreadResponse} from '@/api/types'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

export async function listThreads(boardSlug: string): Promise<ThreadResponse[]> {
  const { data, error } = await apiClient.GET('/api/{board_slug}/threads', {
    params: { path: { board_slug: boardSlug } },
  })
  if (error) throw error
  return data
}

export async function getThread(
  boardSlug: string,
  threadId: number,
): Promise<ThreadDetailResponse> {
  const { data, error } = await apiClient.GET('/api/{board_slug}/threads/{thread_id}', {
    params: { path: { board_slug: boardSlug, thread_id: threadId } },
  })
  if (error) throw error
  return data
}

export interface ThreadFields {
  title?: string
  name?: string
  body?: string
  sage?: boolean
}

// multipart/form-data — openapi-fetch does not cleanly support nested form
// schemas, so we use fetch directly and build FormData manually.
export async function createThread(
  boardSlug: string,
  fields: ThreadFields,
  files: File[],
  captchaToken: string,
  captchaAnswer: string,
): Promise<ThreadDetailResponse> {
  const formData = new FormData()
  if (fields.title) formData.append('title', fields.title)
  if (fields.name) formData.append('name', fields.name)
  if (fields.body) formData.append('body', fields.body)
  formData.append('sage', fields.sage ? 'true' : 'false')
  for (const file of files) {
    formData.append('files', file)
  }

  const response = await fetch(`${API_BASE}/api/${boardSlug}/threads`, {
    method: 'POST',
    headers: {
      'X-Captcha-Token': captchaToken,
      'X-Captcha-Answer': captchaAnswer,
    },
    body: formData,
  })

  if (!response.ok) {
    throw await response.json().catch(() => ({detail: response.statusText}))
  }

  return await response.json() as Promise<ThreadDetailResponse>
}

