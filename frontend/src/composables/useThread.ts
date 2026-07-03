import { useQuery } from '@tanstack/vue-query'
import type { Ref } from 'vue'
import { getThread } from '@/api/threads'
import type { PostResponse, ThreadDetailResponse } from '@/api/types'

export function threadQueryKey(slug: string | Ref<string>, id: number | Ref<number>) {
  return ['thread', slug, id] as const
}

// append a post to a cached thread, deduped by id and bumping reply_count to
// match the server (which increments it on every reply). shared by the
// optimistic reply append and the live new_post websocket event so both paths
// stay consistent and a post added by one cannot be doubled by the other.
// can_edit is viewer-specific and the broadcast websocket copy is always false,
// so when both paths add the same post we keep edit capability if either has it
// (otherwise a websocket frame arriving before the poster's own response would
// hide the Edit button until a reload recomputed it server-side).
export function appendPostToThread(
  thread: ThreadDetailResponse | undefined,
  post: PostResponse,
): ThreadDetailResponse | undefined {
  if (!thread) return thread

  const posts = thread.posts ?? []
  const existing = posts.find((candidate) => candidate.id === post.id)
  if (existing) {
    if (post.can_edit && !existing.can_edit) {
      return {
        ...thread,
        posts: posts.map((candidate) =>
          candidate.id === post.id ? { ...candidate, can_edit: true } : candidate,
        ),
      }
    }
    return thread
  }

  return { ...thread, reply_count: thread.reply_count + 1, posts: [...posts, post] }
}

export function useThread(slug: Ref<string>, threadId: Ref<number>) {
  return useQuery({
    queryKey: threadQueryKey(slug, threadId),
    queryFn: () => getThread(slug.value, threadId.value),
  })
}

