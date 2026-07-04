import { onScopeDispose, toValue, watch, type MaybeRefOrGetter } from 'vue'
import { useQueryClient } from '@tanstack/vue-query'

import { threadsPageQueryKey } from '@/composables/useThreads'
import { wsUrl, WS_EVENT, type WsEnvelope } from '@/api/ws'
import type { ThreadResponse } from '@/api/types'

// catalog order matches the backend: stickies first, then most recent bump.
function sortThreads(threads: ThreadResponse[]): ThreadResponse[] {
  return [...threads].sort((a, b) => {
    if (a.is_sticky !== b.is_sticky) return a.is_sticky ? -1 : 1
    return new Date(b.bump_at).getTime() - new Date(a.bump_at).getTime()
  })
}

// subscribes to a board's realtime feed and keeps the first catalog page's
// query cache live: new_thread prepends (deduped by id); thread_updated merges
// lock/sticky flags onto the matching card and re-sorts so a sticky jumps up.
export function useBoardWs(slug: MaybeRefOrGetter<string>) {
  const queryClient = useQueryClient()
  let socket: WebSocket | null = null

  function applyEvent(envelope: WsEnvelope) {
    const key = threadsPageQueryKey(toValue(slug), 1)

    if (envelope.type === WS_EVENT.NEW_THREAD) {
      const thread = envelope.data as ThreadResponse
      queryClient.setQueryData<ThreadResponse[]>(key, (old) => {
        if (!old) return old
        if (old.some((existing) => existing.id === thread.id)) return old
        return [thread, ...old]
      })
    }

    if (envelope.type === WS_EVENT.THREAD_UPDATED) {
      const update = envelope.data as ThreadResponse
      queryClient.setQueryData<ThreadResponse[]>(key, (old) => {
        if (!old) return old
        return sortThreads(
          old.map((existing) =>
            existing.id === update.id
              ? { ...existing, is_locked: update.is_locked, is_sticky: update.is_sticky }
              : existing,
          ),
        )
      })
    }

    if (envelope.type === WS_EVENT.THREAD_DELETED) {
      const { id } = envelope.data as { id: number }
      queryClient.setQueryData<ThreadResponse[]>(key, (old) =>
        old ? old.filter((existing) => existing.id !== id) : old,
      )
    }
  }

  function onMessage(event: MessageEvent) {
    try {
      applyEvent(JSON.parse(event.data as string) as WsEnvelope)
    } catch {
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
