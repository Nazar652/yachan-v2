import { onScopeDispose, toValue, watch, type MaybeRefOrGetter } from 'vue'
import { useQueryClient } from '@tanstack/vue-query'

import { appendPostToThread, threadQueryKey } from '@/composables/useThread'
import { wsUrl, WS_EVENT, type WsEnvelope } from '@/api/ws'
import type { PostResponse, ThreadDetailResponse } from '@/api/types'

// subscribes to a thread's realtime feed and merges events into the thread
// query cache: new_post appends, post_edited replaces. appends are deduped by
// post id because the poster also appended their own reply optimistically.
export function useThreadWs(
  slug: MaybeRefOrGetter<string>,
  threadId: MaybeRefOrGetter<number>,
) {
  const queryClient = useQueryClient()
  let socket: WebSocket | null = null

  function applyEvent(envelope: WsEnvelope) {
    const key = threadQueryKey(toValue(slug), toValue(threadId))

    if (envelope.type === WS_EVENT.NEW_POST) {
      const post = envelope.data as PostResponse
      queryClient.setQueryData<ThreadDetailResponse>(key, (old) => appendPostToThread(old, post))
    } else if (envelope.type === WS_EVENT.POST_EDITED) {
      const post = envelope.data as PostResponse
      queryClient.setQueryData<ThreadDetailResponse>(key, (old) => {
        if (!old) return old
        return {
          ...old,
          posts: (old.posts ?? []).map((existing) =>
            existing.id === post.id ? post : existing,
          ),
        }
      })
    }
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
    socket = new WebSocket(wsUrl(`/${toValue(slug)}/threads/${toValue(threadId)}/ws`))
    socket.onmessage = onMessage
  }

  connect()
  watch(() => [toValue(slug), toValue(threadId)], connect)
  onScopeDispose(close)

  return { close }
}
