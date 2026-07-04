import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { defineComponent } from 'vue'
import { mount } from '@vue/test-utils'

import { useReconnectingWs } from '@/composables/useReconnectingWs'

class MockWebSocket {
  static instances: MockWebSocket[] = []
  url: string
  onopen: (() => void) | null = null
  onmessage: ((event: { data: string }) => void) | null = null
  onclose: (() => void) | null = null
  close = vi.fn()
  constructor(url: string) {
    this.url = url
    MockWebSocket.instances.push(this)
  }
}

beforeEach(() => {
  MockWebSocket.instances = []
  vi.stubGlobal('WebSocket', MockWebSocket)
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
  vi.unstubAllGlobals()
})

function lastSocket(): MockWebSocket {
  return MockWebSocket.instances[MockWebSocket.instances.length - 1] as MockWebSocket
}

function mountWs(path = '/b/ws', onEnvelope = vi.fn()) {
  const Host = defineComponent({
    setup() {
      useReconnectingWs(() => path, onEnvelope)
      return () => null
    },
  })
  return { wrapper: mount(Host), onEnvelope }
}

describe('useReconnectingWs', () => {
  it('opens a socket to the /api-prefixed url', () => {
    mountWs('/b/ws')
    expect(MockWebSocket.instances).toHaveLength(1)
    expect(lastSocket().url).toMatch(/\/api\/b\/ws$/)
  })

  it('forwards decoded envelopes to the handler', () => {
    const { onEnvelope } = mountWs('/b/ws')
    lastSocket().onmessage?.({ data: JSON.stringify({ type: 'new_thread', data: { id: 1 } }) })
    expect(onEnvelope).toHaveBeenCalledWith({ type: 'new_thread', data: { id: 1 } })
  })

  it('ignores malformed frames', () => {
    const { onEnvelope } = mountWs('/b/ws')
    lastSocket().onmessage?.({ data: 'not json' })
    expect(onEnvelope).not.toHaveBeenCalled()
  })

  it('reconnects after an unexpected drop', () => {
    mountWs('/b/ws')
    lastSocket().onclose?.()
    vi.advanceTimersByTime(1000)
    expect(MockWebSocket.instances).toHaveLength(2)
  })

  it('grows the backoff on repeated drops and resets it on a successful open', () => {
    mountWs('/b/ws')
    lastSocket().onclose?.()
    vi.advanceTimersByTime(1000) // first backoff 1s -> socket 2
    expect(MockWebSocket.instances).toHaveLength(2)

    lastSocket().onclose?.()
    vi.advanceTimersByTime(1000) // second backoff is 2s, not yet
    expect(MockWebSocket.instances).toHaveLength(2)
    vi.advanceTimersByTime(1000) // 2s elapsed -> socket 3
    expect(MockWebSocket.instances).toHaveLength(3)

    lastSocket().onopen?.() // healthy again resets the backoff
    lastSocket().onclose?.()
    vi.advanceTimersByTime(1000) // back to 1s -> socket 4
    expect(MockWebSocket.instances).toHaveLength(4)
  })

  it('fires onReconnect after a drop-triggered reopen, not on the first open', () => {
    const onReconnect = vi.fn()
    const Host = defineComponent({
      setup() {
        useReconnectingWs(() => '/b/ws', vi.fn(), onReconnect)
        return () => null
      },
    })
    mount(Host)
    lastSocket().onopen?.() // first open — not a reconnect
    expect(onReconnect).not.toHaveBeenCalled()

    lastSocket().onclose?.() // drop
    vi.advanceTimersByTime(1000) // reconnect -> socket 2
    lastSocket().onopen?.() // reopen
    expect(onReconnect).toHaveBeenCalledTimes(1)
  })

  it('stops reconnecting once the scope is disposed', () => {
    const { wrapper } = mountWs('/b/ws')
    const socket = lastSocket()
    wrapper.unmount()
    expect(socket.close).toHaveBeenCalled()
    socket.onclose?.() // a late close event must not schedule anything
    vi.advanceTimersByTime(60000)
    expect(MockWebSocket.instances).toHaveLength(1)
  })
})
