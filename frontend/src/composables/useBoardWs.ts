import { onScopeDispose, toValue, watch, type MaybeRefOrGetter } from 'vue'
import { useQueryClient } from '@tanstack/vue-query'

import { threadsPageQueryKey } from '@/composables/useThreads'
import { wsUrl, WS_EVENT, type WsEnvelope } from '@/api/ws'
import type { ThreadResponse } from '@/api/types'

// subscribes to a board's realtime feed and prepends new threads to the
// first catalog page's query cache (deduped by thread id).
export function useBoardWs(slug: MaybeRefOrGetter<string>) {
  const queryClient = useQueryClient()
  let socket: WebSocket | null = null

  function applyEvent(envelope: WsEnvelope) {
    if (envelope.type !== WS_EVENT.NEW_THREAD) return
    const thread = envelope.data as ThreadResponse
    queryClient.setQueryData<ThreadResponse[]>(threadsPageQueryKey(toValue(slug), 1), (old) => {
      if (!old) return old
      if (old.some((existing) => existing.id === thread.id)) return old
      return [thread, ...old]
    })
  }

  function onMessage(event: MessageEvent) {
    try {
      applyEvent(JSON.parse(event.data as string) as WsEnvelope)
    } catch {
      // ignore malformed frames
    }
  }

  function close() {
    if (socket) {
      socket.onmessage = null
      socket.close()
      socket = null
    }
  }

  function connect() {
    close()
    socket = new WebSocket(wsUrl(`/${toValue(slug)}/ws`))
    socket.onmessage = onMessage
  }

  connect()
  watch(() => toValue(slug), connect)
  onScopeDispose(close)

  return { close }
}
