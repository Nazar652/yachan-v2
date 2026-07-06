import { beforeEach, describe, expect, it, vi } from 'vitest'

import { WATCHED_THREADS_STORAGE_KEY } from '@/composables/useWatchedThreads'

// the composable keeps module-level shared state seeded from localStorage at
// import time, so each test resets the module registry to get a fresh instance
async function freshModule() {
  vi.resetModules()
  return import('@/composables/useWatchedThreads')
}

function thread(overrides: Partial<{ id: number; slug: string; title: string | null; reply_count: number }> = {}) {
  return { id: 1, slug: 'b', title: 'hello', reply_count: 3, ...overrides }
}

beforeEach(() => {
  localStorage.clear()
})

describe('useWatchedThreads', () => {
  it('starts empty and reports threads as not watched', async () => {
    const { useWatchedThreads } = await freshModule()
    const { isWatched, watched } = useWatchedThreads()
    expect(isWatched(1)).toBe(false)
    expect(watched.value).toEqual([])
  })

  it('toggle adds a thread seeded with the current reply_count as lastSeenReplyCount', async () => {
    const { useWatchedThreads } = await freshModule()
    const { toggle, isWatched, watched } = useWatchedThreads()

    toggle(thread())

    expect(isWatched(1)).toBe(true)
    expect(watched.value).toEqual([
      { threadId: 1, slug: 'b', title: 'hello', lastSeenReplyCount: 3, addedAt: expect.any(String) },
    ])
  })

  it('toggle removes an already-watched thread', async () => {
    const { useWatchedThreads } = await freshModule()
    const { toggle, isWatched } = useWatchedThreads()

    toggle(thread())
    toggle(thread())

    expect(isWatched(1)).toBe(false)
  })

  it('remove drops a watched thread', async () => {
    const { useWatchedThreads } = await freshModule()
    const { toggle, remove, isWatched } = useWatchedThreads()

    toggle(thread())
    remove(1)

    expect(isWatched(1)).toBe(false)
  })

  it('markSeen bumps lastSeenReplyCount forward', async () => {
    const { useWatchedThreads } = await freshModule()
    const { toggle, markSeen, watched } = useWatchedThreads()

    toggle(thread({ reply_count: 3 }))
    markSeen(1, 7)

    expect(watched.value[0]?.lastSeenReplyCount).toBe(7)
  })

  it('markSeen never moves lastSeenReplyCount backward', async () => {
    const { useWatchedThreads } = await freshModule()
    const { toggle, markSeen, watched } = useWatchedThreads()

    toggle(thread({ reply_count: 5 }))
    markSeen(1, 2)

    expect(watched.value[0]?.lastSeenReplyCount).toBe(5)
  })

  it('markSeen is a no-op for a thread that is not watched', async () => {
    const { useWatchedThreads } = await freshModule()
    const { markSeen, watched } = useWatchedThreads()

    markSeen(999, 10)

    expect(watched.value).toEqual([])
  })

  it('persists the watch list to localStorage', async () => {
    const { useWatchedThreads } = await freshModule()
    useWatchedThreads().toggle(thread())

    const stored = JSON.parse(localStorage.getItem(WATCHED_THREADS_STORAGE_KEY)!)
    expect(stored).toHaveLength(1)
    expect(stored[0]).toMatchObject({ threadId: 1, slug: 'b', title: 'hello', lastSeenReplyCount: 3 })
  })

  it('restores the watch list stored from a previous session', async () => {
    localStorage.setItem(
      WATCHED_THREADS_STORAGE_KEY,
      JSON.stringify([{ threadId: 1, slug: 'b', title: 'hello', lastSeenReplyCount: 3, addedAt: '2026-01-01T00:00:00.000Z' }]),
    )
    const { useWatchedThreads } = await freshModule()
    expect(useWatchedThreads().isWatched(1)).toBe(true)
  })

  it('falls back to an empty list on malformed storage', async () => {
    localStorage.setItem(WATCHED_THREADS_STORAGE_KEY, 'not json')
    const { useWatchedThreads } = await freshModule()
    expect(useWatchedThreads().watched.value).toEqual([])
  })

  it('drops malformed entries but keeps well-formed ones', async () => {
    localStorage.setItem(
      WATCHED_THREADS_STORAGE_KEY,
      JSON.stringify([
        { threadId: 1, slug: 'b', title: 'hello', lastSeenReplyCount: 3, addedAt: '2026-01-01T00:00:00.000Z' },
        { threadId: 'nope' },
      ]),
    )
    const { useWatchedThreads } = await freshModule()
    const { watched } = useWatchedThreads()
    expect(watched.value).toHaveLength(1)
    expect(watched.value[0]?.threadId).toBe(1)
  })
})
