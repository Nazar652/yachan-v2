import { beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent } from 'vue'
import { mount, flushPromises } from '@vue/test-utils'
import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query'

import { getThreadStatuses } from '@/api/threads'

vi.mock('@/api/threads', () => ({
  getThreadStatuses: vi.fn(),
}))

const getThreadStatusesMock = vi.mocked(getThreadStatuses)

// useWatcherStatus builds on the module-level shared state of useWatchedThreads,
// so each test resets the module registry to start from an empty watch list
async function freshModules() {
  vi.resetModules()
  const watchedModule = await import('@/composables/useWatchedThreads')
  const statusModule = await import('@/composables/useWatcherStatus')
  return { ...watchedModule, ...statusModule }
}

function mountWatcherStatus(
  useWatcherStatus: Awaited<ReturnType<typeof freshModules>>['useWatcherStatus'],
) {
  let api!: ReturnType<typeof useWatcherStatus>
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const Host = defineComponent({
    setup() {
      api = useWatcherStatus()
      return () => null
    },
  })
  mount(Host, { global: { plugins: [[VueQueryPlugin, { queryClient }]] } })
  return api
}

beforeEach(() => {
  localStorage.clear()
  getThreadStatusesMock.mockReset()
})

describe('useWatcherStatus', () => {
  it('does not query the api when nothing is watched', async () => {
    const { useWatcherStatus } = await freshModules()
    mountWatcherStatus(useWatcherStatus)
    await flushPromises()
    expect(getThreadStatusesMock).not.toHaveBeenCalled()
  })

  it('computes an unread count from reply_count minus lastSeenReplyCount', async () => {
    const { useWatchedThreads, useWatcherStatus } = await freshModules()
    useWatchedThreads().toggle({ id: 1, slug: 'b', title: 'hi', reply_count: 3 })
    getThreadStatusesMock.mockResolvedValue([
      { id: 1, board_slug: 'b', title: 'hi', is_locked: false, reply_count: 5, bump_at: '' },
    ])

    const api = mountWatcherStatus(useWatcherStatus)
    await flushPromises()

    expect(getThreadStatusesMock).toHaveBeenCalledWith([1])
    expect(api.watchedStatuses.value).toEqual([
      { threadId: 1, slug: 'b', title: 'hi', unread: 2, dead: false },
    ])
    expect(api.unreadByThreadId.value.get(1)).toBe(2)
    expect(api.totalUnread.value).toBe(2)
  })

  it('clamps unread to zero when the server count is not ahead', async () => {
    const { useWatchedThreads, useWatcherStatus } = await freshModules()
    useWatchedThreads().toggle({ id: 1, slug: 'b', title: 'hi', reply_count: 5 })
    getThreadStatusesMock.mockResolvedValue([
      { id: 1, board_slug: 'b', title: 'hi', is_locked: false, reply_count: 5, bump_at: '' },
    ])

    const api = mountWatcherStatus(useWatcherStatus)
    await flushPromises()

    expect(api.totalUnread.value).toBe(0)
  })

  it('marks a thread missing from the response as dead', async () => {
    const { useWatchedThreads, useWatcherStatus } = await freshModules()
    useWatchedThreads().toggle({ id: 1, slug: 'b', title: 'hi', reply_count: 3 })
    getThreadStatusesMock.mockResolvedValue([])

    const api = mountWatcherStatus(useWatcherStatus)
    await flushPromises()

    expect(api.watchedStatuses.value).toEqual([
      { threadId: 1, slug: 'b', title: 'hi', unread: 0, dead: true },
    ])
  })

  it('sums unread across multiple watched threads for totalUnread', async () => {
    const { useWatchedThreads, useWatcherStatus } = await freshModules()
    const { toggle } = useWatchedThreads()
    toggle({ id: 1, slug: 'b', title: 'a', reply_count: 1 })
    toggle({ id: 2, slug: 'g', title: 'b', reply_count: 2 })
    getThreadStatusesMock.mockResolvedValue([
      { id: 1, board_slug: 'b', title: 'a', is_locked: false, reply_count: 4, bump_at: '' },
      { id: 2, board_slug: 'g', title: 'b', is_locked: false, reply_count: 3, bump_at: '' },
    ])

    const api = mountWatcherStatus(useWatcherStatus)
    await flushPromises()

    expect(api.totalUnread.value).toBe(4)
  })
})
