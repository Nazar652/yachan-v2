import { apiClient } from '@/api/client'
import { toApiError } from '@/api/errors'
import type {
  LatestThreadResponse,
  PostResponse,
  ThreadDetailResponse,
  ThreadResponse,
} from '@/api/types'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

export async function listThreads(
  boardSlug: string,
  limit = 50,
  offset = 0,
): Promise<ThreadResponse[]> {
  const { data, error, response } = await apiClient.GET('/api/{board_slug}/threads', {
    params: { path: { board_slug: boardSlug }, query: { limit, offset } },
  })
  if (error) throw toApiError(error, response)
  return data
}

export async function listLatestThreads(limit = 5): Promise<LatestThreadResponse[]> {
  const { data, error, response } = await apiClient.GET('/api/threads/latest', {
    params: { query: { limit } },
  })
  if (error) throw toApiError(error, response)
  return data
}

export async function getThread(
  boardSlug: string,
  threadId: number,
): Promise<ThreadDetailResponse> {
  const { data, error, response } = await apiClient.GET('/api/{board_slug}/threads/{thread_id}', {
    params: { path: { board_slug: boardSlug, thread_id: threadId } },
  })
  if (error) throw toApiError(error, response)
  return data
}

export interface ThreadFields {
  title?: string
  name?: string
  body?: string
  sage?: boolean
}

// openapi-fetch does not cleanly support nested form schemas, so we use fetch directly and build FormData manually.
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
    const body = await response.json().catch(() => ({ detail: response.statusText }))
    throw toApiError(body, response.status)
  }

  return await response.json() as Promise<ThreadDetailResponse>
}

export interface ReplyFields {
  name?: string
  body?: string
  sage?: boolean
}

// a reply needs no title and its image is optional.
export async function createReply(
  boardSlug: string,
  threadId: number,
  fields: ReplyFields,
  files: File[],
  captchaToken: string,
  captchaAnswer: string,
): Promise<PostResponse> {
  const formData = new FormData()
  if (fields.name) formData.append('name', fields.name)
  if (fields.body) formData.append('body', fields.body)
  formData.append('sage', fields.sage ? 'true' : 'false')
  for (const file of files) {
    formData.append('files', file)
  }

  const response = await fetch(`${API_BASE}/api/${boardSlug}/threads/${threadId}/posts`, {
    method: 'POST',
    headers: {
      'X-Captcha-Token': captchaToken,
      'X-Captcha-Answer': captchaAnswer,
    },
    body: formData,
  })

  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }))
    throw toApiError(body, response.status)
  }

  return await response.json() as Promise<PostResponse>
}

