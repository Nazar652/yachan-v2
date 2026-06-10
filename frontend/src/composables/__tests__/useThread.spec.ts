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

  it('upgrades can_edit when the same post is re-added with edit capability', () => {
    const existing = thread({ posts: [{ id: 1, post_number: 1, can_edit: false } as PostResponse] })
    const authoritative = { id: 1, post_number: 1, can_edit: true } as PostResponse
    const result = appendPostToThread(existing, authoritative)
    expect(result?.posts?.[0]?.can_edit).toBe(true)
    // it is still the same post, not a duplicate, and reply_count is untouched
    expect(result?.posts).toHaveLength(1)
    expect(result?.reply_count).toBe(1)
  })

  it('never downgrades can_edit when a broadcast copy lacks it', () => {
    const existing = thread({ posts: [{ id: 1, post_number: 1, can_edit: true } as PostResponse] })
    const broadcast = { id: 1, post_number: 1, can_edit: false } as PostResponse
    const result = appendPostToThread(existing, broadcast)
    expect(result).toBe(existing)
    expect(result?.posts?.[0]?.can_edit).toBe(true)
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
