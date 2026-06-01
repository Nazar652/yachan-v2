import { describe, expect, it } from 'vitest'

import { appendPostToThread, threadQueryKey } from '@/composables/useThread'
import type { PostResponse, ThreadDetailResponse } from '@/api/types'

function thread(overrides: Partial<ThreadDetailResponse> = {}): ThreadDetailResponse {
  return {
    id: 42, board_id: 1, title: 'T', is_locked: false, is_sticky: false,
    reply_count: 1, bump_at: '', created_at: '',
    posts: [{ id: 1, post_number: 1 } as PostResponse],
    ...overrides,
  }
}

describe('threadQueryKey', () => {
  it('builds a stable key from slug and id', () => {
    expect(threadQueryKey('b', 42)).toEqual(['thread', 'b', 42])
  })
})

describe('appendPostToThread', () => {
  it('appends the post and bumps reply_count', () => {
    const post = { id: 2, post_number: 2 } as PostResponse
    expect(appendPostToThread(thread(), post)).toEqual({
      id: 42, board_id: 1, title: 'T', is_locked: false, is_sticky: false,
      reply_count: 2, bump_at: '', created_at: '',
      posts: [{ id: 1, post_number: 1 }, { id: 2, post_number: 2 }],
    })
  })

  it('is a no-op when a post with the same id is already present', () => {
    const existing = thread()
    const duplicate = { id: 1, post_number: 1 } as PostResponse
    const result = appendPostToThread(existing, duplicate)
    expect(result).toBe(existing)
    expect(result?.reply_count).toBe(1)
  })

  it('handles a thread with no posts array', () => {
    const post = { id: 2, post_number: 2 } as PostResponse
    const result = appendPostToThread(thread({ posts: undefined }), post)
    expect(result?.posts).toEqual([{ id: 2, post_number: 2 }])
    expect(result?.reply_count).toBe(2)
  })

  it('passes through undefined', () => {
    expect(appendPostToThread(undefined, { id: 2 } as PostResponse)).toBeUndefined()
  })
})
