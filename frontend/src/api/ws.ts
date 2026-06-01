import type { PostResponse, ThreadResponse } from '@/api/types'

// the backend websocket routes are not part of the openapi schema (ws is not
// rest), so the url and event shapes are declared here by hand.

// http://host → ws://host, https://host → wss://host
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
} as const

// envelope pushed on every channel: { type, data }
export interface WsEnvelope {
  type: string
  data: PostResponse | ThreadResponse
}
