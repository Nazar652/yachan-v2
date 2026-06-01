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

function mountThreadWs(queryClient: QueryClient) {
  const Host = defineComponent({
    setup() {
      useThreadWs('b', 42)
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

  it('appends a new_post to the thread cache', () => {
    const queryClient = new QueryClient()
    queryClient.setQueryData(threadQueryKey('b', 42), { id: 42, posts: [{ id: 1, post_number: 1 }] })
    mountThreadWs(queryClient)

    emit({ type: 'new_post', data: { id: 2, post_number: 2 } })

    expect(queryClient.getQueryData(threadQueryKey('b', 42))).toEqual({
      id: 42,
      posts: [{ id: 1, post_number: 1 }, { id: 2, post_number: 2 }],
    })
  })

  it('ignores a new_post whose id is already in the cache', () => {
    const queryClient = new QueryClient()
    queryClient.setQueryData(threadQueryKey('b', 42), { id: 42, posts: [{ id: 2, post_number: 2 }] })
    mountThreadWs(queryClient)

    emit({ type: 'new_post', data: { id: 2, post_number: 2 } })

    expect(queryClient.getQueryData(threadQueryKey('b', 42))).toEqual({
      id: 42,
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
