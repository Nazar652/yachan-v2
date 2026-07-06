import { computed } from 'vue'
import { useQuery } from '@tanstack/vue-query'

import { getThreadStatuses } from '@/api/threads'
import { useWatchedThreads } from '@/composables/useWatchedThreads'
import type { ThreadStatusResponse } from '@/api/types'

const REFETCH_INTERVAL_MS = 60_000

export function watcherStatusQueryKey(threadIds: number[]) {
  return ['watcher-status', [...threadIds].sort((a, b) => a - b)] as const
}

export interface WatchedThreadStatus {
  threadId: number
  slug: string
  title: string | null
  unread: number
  // true when the thread is missing from the server response (deleted)
  dead: boolean
}

export function useWatcherStatus() {
  const { watched, markSeen, remove } = useWatchedThreads()
  const threadIds = computed(() => watched.value.map((entry) => entry.threadId))

  const query = useQuery({
    queryKey: computed(() => watcherStatusQueryKey(threadIds.value)),
    queryFn: () => getThreadStatuses(threadIds.value),
    enabled: computed(() => threadIds.value.length > 0),
    refetchInterval: REFETCH_INTERVAL_MS,
  })

  const statusByThreadId = computed(() => {
    const map = new Map<number, ThreadStatusResponse>()
    for (const status of query.data.value ?? []) {
      map.set(status.id, status)
    }
    return map
  })

  const watchedStatuses = computed<WatchedThreadStatus[]>(() =>
    watched.value.map((entry) => {
      const status = statusByThreadId.value.get(entry.threadId)
      if (!status) {
        return {
          threadId: entry.threadId,
          slug: entry.slug,
          title: entry.title,
          unread: 0,
          dead: true,
        }
      }
      return {
        threadId: entry.threadId,
        slug: status.board_slug,
        title: status.title,
        unread: Math.max(0, status.reply_count - entry.lastSeenReplyCount),
        dead: false,
      }
    }),
  )

  const unreadByThreadId = computed(() => {
    const map = new Map<number, number>()
    for (const status of watchedStatuses.value) map.set(status.threadId, status.unread)
    return map
  })

  const totalUnread = computed(() =>
    watchedStatuses.value.reduce((sum, status) => sum + status.unread, 0),
  )

  return { ...query, watchedStatuses, unreadByThreadId, totalUnread, markSeen, remove }
}
