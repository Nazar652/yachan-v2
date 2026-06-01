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
export function appendPostToThread(
  thread: ThreadDetailResponse | undefined,
  post: PostResponse,
): ThreadDetailResponse | undefined {
  if (!thread) return thread
  const posts = thread.posts ?? []
  if (posts.some((existing) => existing.id === post.id)) return thread
  return { ...thread, reply_count: thread.reply_count + 1, posts: [...posts, post] }
}

export function useThread(slug: Ref<string>, threadId: Ref<number>) {
  return useQuery({
    queryKey: threadQueryKey(slug, threadId),
    queryFn: () => getThread(slug.value, threadId.value),
  })
}

