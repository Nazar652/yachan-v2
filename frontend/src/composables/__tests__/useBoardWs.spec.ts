import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { defineComponent } from 'vue'
import { mount } from '@vue/test-utils'
import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query'

import { useBoardWs } from '@/composables/useBoardWs'
import { threadsPageQueryKey } from '@/composables/useThreads'

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

function mountBoardWs(queryClient: QueryClient) {
  const Host = defineComponent({
    setup() {
      useBoardWs('b')
      return () => null
    },
  })
  return mount(Host, { global: { plugins: [[VueQueryPlugin, { queryClient }]] } })
}

describe('useBoardWs', () => {
  it('opens a websocket to the board feed url', () => {
    mountBoardWs(new QueryClient())
    expect(MockWebSocket.instances).toHaveLength(1)
    expect(lastSocket().url).toMatch(/\/api\/b\/ws$/)
  })

  it('prepends a new_thread to the catalog cache', () => {
    const queryClient = new QueryClient()
    queryClient.setQueryData(threadsPageQueryKey('b', 1), [{ id: 1, title: 'first' }])
    mountBoardWs(queryClient)

    emit({ type: 'new_thread', data: { id: 2, title: 'second' } })

    expect(queryClient.getQueryData(threadsPageQueryKey('b', 1))).toEqual([
      { id: 2, title: 'second' },
      { id: 1, title: 'first' },
    ])
  })

  it('ignores a new_thread whose id is already in the cache', () => {
    const queryClient = new QueryClient()
    queryClient.setQueryData(threadsPageQueryKey('b', 1), [{ id: 2, title: 'second' }])
    mountBoardWs(queryClient)

    emit({ type: 'new_thread', data: { id: 2, title: 'second' } })

    expect(queryClient.getQueryData(threadsPageQueryKey('b', 1))).toEqual([{ id: 2, title: 'second' }])
  })

  it('merges flags and re-sorts a stickied thread to the top on thread_updated', () => {
    const queryClient = new QueryClient()
    queryClient.setQueryData(threadsPageQueryKey('b', 1), [
      { id: 1, is_sticky: false, is_locked: false, bump_at: '2026-01-02T00:00:00+00:00' },
      { id: 2, is_sticky: false, is_locked: false, bump_at: '2026-01-01T00:00:00+00:00' },
    ])
    mountBoardWs(queryClient)

    emit({ type: 'thread_updated', data: { id: 2, is_sticky: true, is_locked: false } })

    expect(queryClient.getQueryData(threadsPageQueryKey('b', 1))).toEqual([
      { id: 2, is_sticky: true, is_locked: false, bump_at: '2026-01-01T00:00:00+00:00' },
      { id: 1, is_sticky: false, is_locked: false, bump_at: '2026-01-02T00:00:00+00:00' },
    ])
  })

  it('leaves other threads untouched when locking one on thread_updated', () => {
    const queryClient = new QueryClient()
    queryClient.setQueryData(threadsPageQueryKey('b', 1), [
      { id: 1, is_sticky: false, is_locked: false, bump_at: '2026-01-02T00:00:00+00:00' },
      { id: 2, is_sticky: false, is_locked: false, bump_at: '2026-01-01T00:00:00+00:00' },
    ])
    mountBoardWs(queryClient)

    emit({ type: 'thread_updated', data: { id: 1, is_sticky: false, is_locked: true } })

    expect(queryClient.getQueryData(threadsPageQueryKey('b', 1))).toEqual([
      { id: 1, is_sticky: false, is_locked: true, bump_at: '2026-01-02T00:00:00+00:00' },
      { id: 2, is_sticky: false, is_locked: false, bump_at: '2026-01-01T00:00:00+00:00' },
    ])
  })

  it('drops a thread from the catalog cache on thread_deleted', () => {
    const queryClient = new QueryClient()
    queryClient.setQueryData(threadsPageQueryKey('b', 1), [
      { id: 1, title: 'first' },
      { id: 2, title: 'second' },
    ])
    mountBoardWs(queryClient)

    emit({ type: 'thread_deleted', data: { id: 1 } })

    expect(queryClient.getQueryData(threadsPageQueryKey('b', 1))).toEqual([{ id: 2, title: 'second' }])
  })

  it('ignores unrelated event types', () => {
    const queryClient = new QueryClient()
    queryClient.setQueryData(threadsPageQueryKey('b', 1), [{ id: 1, title: 'first' }])
    mountBoardWs(queryClient)

    emit({ type: 'new_post', data: { id: 9, post_number: 9 } })

    expect(queryClient.getQueryData(threadsPageQueryKey('b', 1))).toEqual([{ id: 1, title: 'first' }])
  })

  it('closes the socket when the component unmounts', () => {
    const wrapper = mountBoardWs(new QueryClient())
    const socket = lastSocket()
    wrapper.unmount()
    expect(socket.close).toHaveBeenCalled()
  })
})
