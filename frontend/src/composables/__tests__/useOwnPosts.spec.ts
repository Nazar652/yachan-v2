import { beforeEach, describe, expect, it, vi } from 'vitest'

import { OWN_POSTS_STORAGE_KEY } from '@/composables/useOwnPosts'

// the composable keeps module-level shared state seeded from localStorage at
// import time, so each test resets the module registry to get a fresh instance
async function freshModule() {
  vi.resetModules()
  return import('@/composables/useOwnPosts')
}

beforeEach(() => {
  localStorage.clear()
})

describe('useOwnPosts', () => {
  it('starts empty and reports posts as not owned', async () => {
    const { useOwnPosts } = await freshModule()
    const { isOwn, ownNumbers } = useOwnPosts('b')
    expect(isOwn(101)).toBe(false)
    expect(ownNumbers.value.size).toBe(0)
  })

  it('marks a post as owned and reflects it through isOwn and ownNumbers', async () => {
    const { useOwnPosts } = await freshModule()
    const { isOwn, markOwn, ownNumbers } = useOwnPosts('b')
    markOwn(101)
    expect(isOwn(101)).toBe(true)
    expect([...ownNumbers.value]).toEqual([101])
  })

  it('persists owned posts to localStorage grouped by slug', async () => {
    const { useOwnPosts } = await freshModule()
    useOwnPosts('b').markOwn(101)
    useOwnPosts('g').markOwn(202)
    expect(JSON.parse(localStorage.getItem(OWN_POSTS_STORAGE_KEY)!)).toEqual({ b: [101], g: [202] })
  })

  it('keeps ownership scoped per board', async () => {
    const { useOwnPosts } = await freshModule()
    useOwnPosts('b').markOwn(101)
    expect(useOwnPosts('g').isOwn(101)).toBe(false)
  })

  it('does not duplicate a post marked twice', async () => {
    const { useOwnPosts } = await freshModule()
    const board = useOwnPosts('b')
    board.markOwn(101)
    board.markOwn(101)
    expect([...board.ownNumbers.value]).toEqual([101])
  })

  it('restores owned posts stored from a previous session', async () => {
    localStorage.setItem(OWN_POSTS_STORAGE_KEY, JSON.stringify({ b: [101, 102] }))
    const { useOwnPosts } = await freshModule()
    const { isOwn } = useOwnPosts('b')
    expect(isOwn(101)).toBe(true)
    expect(isOwn(102)).toBe(true)
  })

  it('falls back to empty state on malformed storage', async () => {
    localStorage.setItem(OWN_POSTS_STORAGE_KEY, 'not json')
    const { useOwnPosts } = await freshModule()
    expect(useOwnPosts('b').isOwn(101)).toBe(false)
  })
})
