import type { PostResponse, ThreadResponse } from '@/api/types'

// the backend websocket routes are not part of the openapi schema (ws is not
// rest), so the url and event shapes are declared here by hand.

export function toWsBase(apiBase: string): string {
  return apiBase.replace(/^http/, 'ws')
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''
const WS_BASE = (import.meta.env.VITE_WS_BASE_URL as string | undefined) ?? toWsBase(API_BASE)

// path is relative to the /api prefix, e.g. "/b/threads/42/ws"
export function wsUrl(path: string): string {
  return `${WS_BASE}/api${path}`
}

export const WS_EVENT = {
  NEW_POST: 'new_post',
  POST_EDITED: 'post_edited',
  NEW_THREAD: 'new_thread',
  THREAD_UPDATED: 'thread_updated',
  THREAD_DELETED: 'thread_deleted',
  ATTACHMENT_MODERATED: 'attachment_moderated',
  THREAD_SUMMARIZED: 'thread_summarized',
} as const

export interface AttachmentModeratedData {
  attachment_id: number
  post_id: number
  moderation_status: string
}

export interface ThreadSummarizedData {
  thread_id: number
  summary: string
}

export interface WsEnvelope {
  type: string
  data: PostResponse | ThreadResponse | AttachmentModeratedData | ThreadSummarizedData
}
