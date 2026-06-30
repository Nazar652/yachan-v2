import { describe, expect, it, vi, beforeEach } from 'vitest'
import { defineComponent } from 'vue'
import { mount } from '@vue/test-utils'
import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query'

import { useModeration } from '@/composables/useModeration'
import { threadQueryKey } from '@/composables/useThread'
import { threadsPageQueryKey, threadsQueryKey } from '@/composables/useThreads'
import { banPoster, deletePost, deleteThread, setThreadLocked, setThreadSticky } from '@/api/mod'

vi.mock('@/api/mod', () => ({
  setThreadLocked: vi.fn(),
  setThreadSticky: vi.fn(),
  deletePost: vi.fn(),
  deleteThread: vi.fn(),
  banPoster: vi.fn(),
}))

const setThreadLockedMock = vi.mocked(setThreadLocked)
const setThreadStickyMock = vi.mocked(setThreadSticky)
const deletePostMock = vi.mocked(deletePost)
const deleteThreadMock = vi.mocked(deleteThread)
const banPosterMock = vi.mocked(banPoster)

beforeEach(() => {
  setThreadLockedMock.mockReset().mockResolvedValue(undefined)
  setThreadStickyMock.mockReset().mockResolvedValue(undefined)
  deletePostMock.mockReset().mockResolvedValue(undefined)
  deleteThreadMock.mockReset().mockResolvedValue(undefined)
  banPosterMock.mockReset()
})

function mountModeration(queryClient: QueryClient) {
  let api!: ReturnType<typeof useModeration>
  const Host = defineComponent({
    setup() {
      api = useModeration('b', 42)
      return () => null
    },
  })
  mount(Host, { global: { plugins: [[VueQueryPlugin, { queryClient }]] } })
  return api
}

describe('useModeration', () => {
  it('setLocked calls the api, patches the thread cache and invalidates the catalog', async () => {
    const queryClient = new QueryClient()
    queryClient.setQueryData(threadQueryKey('b', 42), { id: 42, is_locked: false })
    const invalidate = vi.spyOn(queryClient, 'invalidateQueries')
    const api = mountModeration(queryClient)

    await api.setLocked(true)

    expect(setThreadLockedMock).toHaveBeenCalledWith('b', 42, true)
    expect(queryClient.getQueryData(threadQueryKey('b', 42))).toEqual({ id: 42, is_locked: true })
    expect(invalidate).toHaveBeenCalledWith({ queryKey: threadsQueryKey('b') })
  })

  it('setSticky calls the api and patches is_sticky', async () => {
    const queryClient = new QueryClient()
    queryClient.setQueryData(threadQueryKey('b', 42), { id: 42, is_sticky: false })
    const api = mountModeration(queryClient)

    await api.setSticky(true)

    expect(setThreadStickyMock).toHaveBeenCalledWith('b', 42, true)
    expect(queryClient.getQueryData(threadQueryKey('b', 42))).toEqual({ id: 42, is_sticky: true })
  })

  it('removePost deletes via the api, drops the post and decrements reply_count', async () => {
    const queryClient = new QueryClient()
    queryClient.setQueryData(threadQueryKey('b', 42), {
      id: 42,
      reply_count: 1,
      posts: [
        { id: 1, post_number: 1, is_op: true },
        { id: 2, post_number: 2, is_op: false },
      ],
    })
    const api = mountModeration(queryClient)

    await api.removePost(2)

    expect(deletePostMock).toHaveBeenCalledWith('b', 2)
    expect(queryClient.getQueryData(threadQueryKey('b', 42))).toEqual({
      id: 42,
      reply_count: 0,
      posts: [{ id: 1, post_number: 1, is_op: true }],
    })
  })

  it('removePost leaves reply_count untouched when the op is deleted', async () => {
    const queryClient = new QueryClient()
    queryClient.setQueryData(threadQueryKey('b', 42), {
      id: 42,
      reply_count: 3,
      posts: [{ id: 1, post_number: 1, is_op: true }],
    })
    const api = mountModeration(queryClient)

    await api.removePost(1)

    expect(queryClient.getQueryData(threadQueryKey('b', 42))).toEqual({
      id: 42,
      reply_count: 3,
      posts: [],
    })
  })

  it('removeThread deletes via the api, drops the card and invalidates the catalog', async () => {
    const queryClient = new QueryClient()
    queryClient.setQueryData(threadsPageQueryKey('b', 1), [
      { id: 42, title: 'doomed' },
      { id: 7, title: 'safe' },
    ])
    const invalidate = vi.spyOn(queryClient, 'invalidateQueries')
    const api = mountModeration(queryClient)

    await api.removeThread()

    expect(deleteThreadMock).toHaveBeenCalledWith('b', 42)
    expect(queryClient.getQueryData(threadsPageQueryKey('b', 1))).toEqual([{ id: 7, title: 'safe' }])
    expect(invalidate).toHaveBeenCalledWith({ queryKey: threadsQueryKey('b') })
  })

  it('ban delegates to banPoster and returns the result', async () => {
    const ban = { id: 9, ip_hash: 'h', board_id: null, reason: 'spam', expires_at: null, is_active: true, created_at: '' }
    banPosterMock.mockResolvedValue(ban as never)
    const api = mountModeration(new QueryClient())

    await expect(api.ban(101, { reason: 'spam' })).resolves.toBe(ban)
    expect(banPosterMock).toHaveBeenCalledWith('b', 101, { reason: 'spam' })
  })
})
