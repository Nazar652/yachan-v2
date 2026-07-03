import { describe, expect, it } from 'vitest'

import { toWsBase, wsUrl, WS_EVENT } from '@/api/ws'

describe('toWsBase', () => {
  it('rewrites http to ws', () => {
    expect(toWsBase('http://localhost:8000')).toBe('ws://localhost:8000')
  })

  it('rewrites https to wss', () => {
    expect(toWsBase('https://example.com')).toBe('wss://example.com')
  })

  it('leaves an empty base empty', () => {
    expect(toWsBase('')).toBe('')
  })
})

describe('wsUrl', () => {
  it('prefixes the api path under the ws base', () => {
    expect(wsUrl('/b/threads/42/ws')).toMatch(/\/api\/b\/threads\/42\/ws$/)
  })
})

describe('WS_EVENT', () => {
  it('matches the backend event type strings', () => {
    expect(WS_EVENT).toEqual({
      NEW_POST: 'new_post',
      POST_EDITED: 'post_edited',
      NEW_THREAD: 'new_thread',
      THREAD_UPDATED: 'thread_updated',
      THREAD_DELETED: 'thread_deleted',
      ATTACHMENT_MODERATED: 'attachment_moderated',
      THREAD_SUMMARIZED: 'thread_summarized',
    })
  })
})
