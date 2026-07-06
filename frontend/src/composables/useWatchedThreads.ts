import { computed, ref } from 'vue'

export const WATCHED_THREADS_STORAGE_KEY = 'yachan_watched_threads'

// threads the visitor chose to watch, kept purely client-side (no accounts on
// an anonymous board). lastSeenReplyCount is the reply_count recorded at the
// last visit/read, used to derive an unread count against the live server count.
export interface WatchedThread {
  threadId: number
  slug: string
  title: string | null
  lastSeenReplyCount: number
  addedAt: string
}

export interface WatchableThread {
  id: number
  slug: string
  title: string | null
  reply_count: number
}

function isWatchedThread(value: unknown): value is WatchedThread {
  if (!value || typeof value !== 'object') return false
  const candidate = value as Record<string, unknown>
  return (
    typeof candidate.threadId === 'number' &&
    typeof candidate.slug === 'string' &&
    (typeof candidate.title === 'string' || candidate.title === null) &&
    typeof candidate.lastSeenReplyCount === 'number' &&
    typeof candidate.addedAt === 'string'
  )
}

function readStored(): WatchedThread[] {
  try {
    const parsed: unknown = JSON.parse(localStorage.getItem(WATCHED_THREADS_STORAGE_KEY) ?? '[]')
    if (!Array.isArray(parsed)) return []
    return parsed.filter(isWatchedThread)
  } catch {
    return []
  }
}

// module-level shared state so the header dropdown and the in-thread/catalog
// star buttons all observe the same watch list
const watchedThreads = ref<WatchedThread[]>(readStored())

function persist() {
  localStorage.setItem(WATCHED_THREADS_STORAGE_KEY, JSON.stringify(watchedThreads.value))
}

export function useWatchedThreads() {
  const watched = computed(() => watchedThreads.value)

  function isWatched(threadId: number): boolean {
    return watchedThreads.value.some((entry) => entry.threadId === threadId)
  }

  function remove(threadId: number) {
    watchedThreads.value = watchedThreads.value.filter((entry) => entry.threadId !== threadId)
    persist()
  }

  function toggle(thread: WatchableThread) {
    if (isWatched(thread.id)) {
      remove(thread.id)
      return
    }
    watchedThreads.value = [
      ...watchedThreads.value,
      {
        threadId: thread.id,
        slug: thread.slug,
        title: thread.title,
        lastSeenReplyCount: thread.reply_count,
        addedAt: new Date().toISOString(),
      },
    ]
    persist()
  }

  function markSeen(threadId: number, replyCount: number) {
    const entry = watchedThreads.value.find((candidate) => candidate.threadId === threadId)
    if (!entry || replyCount <= entry.lastSeenReplyCount) return
    watchedThreads.value = watchedThreads.value.map((candidate) =>
      candidate.threadId === threadId
        ? { ...candidate, lastSeenReplyCount: replyCount }
        : candidate,
    )
    persist()
  }

  return { watched, isWatched, toggle, markSeen, remove }
}
