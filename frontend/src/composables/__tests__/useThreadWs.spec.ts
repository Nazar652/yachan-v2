import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { defineComponent } from 'vue'
import { mount } from '@vue/test-utils'
import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query'

import { useThreadWs } from '@/composables/useThreadWs'
import { threadQueryKey } from '@/composables/useThread'

class MockWebSocket {
  static instances: MockWebSocket[] = []
  url: string
  onmessage: ((event: { data: string }) => void) | null = null
  close = vi.fn()
  constructor(url: string) {
    this.url = url
    MockWebSocket.instances.push(this)
  }
}

beforeEach(() => {
  MockWebSocket.instances = []
  vi.stubGlobal('WebSocket', MockWebSocket)
})

afterEach(() => {
  vi.unstubAllGlobals()
})

function lastSocket(): MockWebSocket {
  return MockWebSocket.instances[MockWebSocket.instances.length - 1] as MockWebSocket
}

function emit(payload: unknown) {
  lastSocket().onmessage?.({ data: JSON.stringify(payload) })
}

function mountThreadWs(queryClient: QueryClient, onThreadDeleted?: () => void) {
  const Host = defineComponent({
    setup() {
      useThreadWs('b', 42, onThreadDeleted)
      return () => null
    },
  })
  return mount(Host, { global: { plugins: [[VueQueryPlugin, { queryClient }]] } })
}

describe('useThreadWs', () => {
  it('opens a websocket to the thread feed url', () => {
    mountThreadWs(new QueryClient())
    expect(MockWebSocket.instances).toHaveLength(1)
    expect(lastSocket().url).toMatch(/\/api\/b\/threads\/42\/ws$/)
  })

  it('appends a new_post to the thread cache and bumps reply_count', () => {
    const queryClient = new QueryClient()
    queryClient.setQueryData(threadQueryKey('b', 42), { id: 42, reply_count: 1, posts: [{ id: 1, post_number: 1 }] })
    mountThreadWs(queryClient)

    emit({ type: 'new_post', data: { id: 2, post_number: 2 } })

    expect(queryClient.getQueryData(threadQueryKey('b', 42))).toEqual({
      id: 42,
      reply_count: 2,
      posts: [{ id: 1, post_number: 1 }, { id: 2, post_number: 2 }],
    })
  })

  it('ignores a new_post whose id is already in the cache (no double bump)', () => {
    const queryClient = new QueryClient()
    queryClient.setQueryData(threadQueryKey('b', 42), { id: 42, reply_count: 1, posts: [{ id: 2, post_number: 2 }] })
    mountThreadWs(queryClient)

    emit({ type: 'new_post', data: { id: 2, post_number: 2 } })

    expect(queryClient.getQueryData(threadQueryKey('b', 42))).toEqual({
      id: 42,
      reply_count: 1,
      posts: [{ id: 2, post_number: 2 }],
    })
  })

  it('replaces an edited post on post_edited', () => {
    const queryClient = new QueryClient()
    queryClient.setQueryData(threadQueryKey('b', 42), { id: 42, posts: [{ id: 1, post_number: 1, body: 'old' }] })
    mountThreadWs(queryClient)

    emit({ type: 'post_edited', data: { id: 1, post_number: 1, body: 'new' } })

    expect(queryClient.getQueryData(threadQueryKey('b', 42))).toEqual({
      id: 42,
      posts: [{ id: 1, post_number: 1, body: 'new' }],
    })
  })

  it('reflects lock/sticky flags on thread_updated', () => {
    const queryClient = new QueryClient()
    queryClient.setQueryData(threadQueryKey('b', 42), {
      id: 42,
      is_locked: false,
      is_sticky: false,
      posts: [{ id: 1, post_number: 1 }],
    })
    mountThreadWs(queryClient)

    emit({ type: 'thread_updated', data: { id: 42, is_locked: true, is_sticky: true } })

    expect(queryClient.getQueryData(threadQueryKey('b', 42))).toEqual({
      id: 42,
      is_locked: true,
      is_sticky: true,
      posts: [{ id: 1, post_number: 1 }],
    })
  })

  it('invalidates the thread query on attachment_moderated', () => {
    const queryClient = new QueryClient()
    const invalidate = vi.spyOn(queryClient, 'invalidateQueries')
    mountThreadWs(queryClient)

    emit({ type: 'attachment_moderated', data: { attachment_id: 3, post_id: 1, moderation_status: 'blocked' } })

    expect(invalidate).toHaveBeenCalledWith({ queryKey: threadQueryKey('b', 42) })
  })

  it('patches the summary into the thread cache on thread_summarized', () => {
    const queryClient = new QueryClient()
    queryClient.setQueryData(threadQueryKey('b', 42), { id: 42, summary: null, posts: [] })
    mountThreadWs(queryClient)

    emit({ type: 'thread_summarized', data: { thread_id: 42, summary: 'a fresh tl;dr' } })

    expect(queryClient.getQueryData(threadQueryKey('b', 42))).toEqual({
      id: 42,
      summary: 'a fresh tl;dr',
      posts: [],
    })
  })

  it('drops the thread cache and notifies the caller on thread_deleted', () => {
    const queryClient = new QueryClient()
    queryClient.setQueryData(threadQueryKey('b', 42), { id: 42, posts: [] })
    const onThreadDeleted = vi.fn()
    mountThreadWs(queryClient, onThreadDeleted)

    emit({ type: 'thread_deleted', data: { id: 42 } })

    expect(queryClient.getQueryData(threadQueryKey('b', 42))).toBeUndefined()
    expect(onThreadDeleted).toHaveBeenCalled()
  })

  it('ignores malformed frames', () => {
    const queryClient = new QueryClient()
    queryClient.setQueryData(threadQueryKey('b', 42), { id: 42, posts: [] })
    mountThreadWs(queryClient)

    lastSocket().onmessage?.({ data: 'not json' })

    expect(queryClient.getQueryData(threadQueryKey('b', 42))).toEqual({ id: 42, posts: [] })
  })

  it('closes the socket when the component unmounts', () => {
    const wrapper = mountThreadWs(new QueryClient())
    const socket = lastSocket()
    wrapper.unmount()
    expect(socket.close).toHaveBeenCalled()
  })
})
