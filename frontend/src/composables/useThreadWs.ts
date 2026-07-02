import { onScopeDispose, toValue, watch, type MaybeRefOrGetter } from 'vue'
import { useQueryClient } from '@tanstack/vue-query'

import { appendPostToThread, threadQueryKey } from '@/composables/useThread'
import { wsUrl, WS_EVENT, type WsEnvelope, type ThreadSummarizedData } from '@/api/ws'
import type { PostResponse, ThreadDetailResponse, ThreadResponse } from '@/api/types'

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
    } else if (envelope.type === WS_EVENT.THREAD_UPDATED) {
      // a mod locked/stickied the thread: reflect the flags so the lock hides
      // the reply form for everyone, not just the mod who flipped it
      const thread = envelope.data as ThreadResponse
      queryClient.setQueryData<ThreadDetailResponse>(key, (old) =>
        old ? { ...old, is_locked: thread.is_locked, is_sticky: thread.is_sticky } : old,
      )
    } else if (envelope.type === WS_EVENT.ATTACHMENT_MODERATED) {
      // attachment visibility depends on the board's 18+ flag, so let the server
      // re-resolve it (hidden attachments come back with a null url)
      void queryClient.invalidateQueries({ queryKey: key })
    } else if (envelope.type === WS_EVENT.THREAD_SUMMARIZED) {
      // a fresh tl;dr landed; the event carries the text, so patch it straight in
      const data = envelope.data as ThreadSummarizedData
      queryClient.setQueryData<ThreadDetailResponse>(key, (old) =>
        old ? { ...old, summary: data.summary } : old,
      )
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
