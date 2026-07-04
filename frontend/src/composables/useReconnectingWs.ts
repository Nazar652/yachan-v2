import { onScopeDispose, toValue, watch, type MaybeRefOrGetter } from 'vue'

import { wsUrl, type WsEnvelope } from '@/api/ws'

// backoff bounds for retrying after an unexpected drop (e.g. a deploy restarts
// the backend): start at 1s, double each attempt, cap at 30s.
const RECONNECT_BASE_MS = 1000
const RECONNECT_MAX_MS = 30000

// a websocket that heals itself: it forwards decoded envelopes to `onEnvelope`
// and, when the connection drops unexpectedly, reconnects with capped exponential
// backoff so the realtime feed recovers without a page reload. an intentional
// close (scope dispose) or a path change (new thread/board) does not backoff.
export function useReconnectingWs(
  path: MaybeRefOrGetter<string>,
  onEnvelope: (envelope: WsEnvelope) => void,
  onReconnect?: () => void,
) {
  let socket: WebSocket | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let attempts = 0
  let disposed = false

  function clearReconnect() {
    if (reconnectTimer !== null) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
  }

  function onMessage(event: MessageEvent) {
    try {
      onEnvelope(JSON.parse(event.data as string) as WsEnvelope)
    } catch {
    }
  }

  function onClose() {
    // unexpected drop: schedule a reconnect unless we closed on purpose
    if (disposed) return
    clearReconnect()
    const delay = Math.min(RECONNECT_BASE_MS * 2 ** attempts, RECONNECT_MAX_MS)
    attempts += 1
    reconnectTimer = setTimeout(connect, delay)
  }

  function detach() {
    if (socket) {
      socket.onopen = null
      socket.onmessage = null
      socket.onclose = null
      socket.close()
      socket = null
    }
  }

  function connect() {
    clearReconnect()
    detach()
    socket = new WebSocket(wsUrl(toValue(path)))
    socket.onopen = () => {
      // after a real drop, envelopes sent during the gap were missed; signal the
      // caller so it can refetch and catch up. a path change resets attempts
      // first, so it is not treated as a reconnect.
      const reconnected = attempts > 0
      attempts = 0
      if (reconnected) onReconnect?.()
    }
    socket.onmessage = onMessage
    socket.onclose = onClose
  }

  function close() {
    disposed = true
    clearReconnect()
    detach()
  }

  connect()
  // a path change is an intentional switch to a new feed — reset the backoff
  watch(
    () => toValue(path),
    () => {
      attempts = 0
      connect()
    },
  )
  onScopeDispose(close)

  return { close }
}
