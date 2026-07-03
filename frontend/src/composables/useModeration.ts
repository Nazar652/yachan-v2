import { toValue, type MaybeRefOrGetter } from 'vue'
import { useQueryClient } from '@tanstack/vue-query'

import { threadQueryKey } from '@/composables/useThread'
import { threadsPageQueryKey, threadsQueryKey } from '@/composables/useThreads'
import {
  banPoster,
  deletePost,
  deleteThread,
  regenerateSummary,
  setThreadLocked,
  setThreadSticky,
} from '@/api/mod'
import type { BanCreate, BanResponse, ThreadDetailResponse, ThreadResponse } from '@/api/types'

// mod-only actions scoped to one thread. each call hits the api, then patches
// the thread cache so the change shows immediately, and invalidates the catalog
// so its lock/sticky icons refresh on the next visit.
export function useModeration(
  slug: MaybeRefOrGetter<string>,
  threadId: MaybeRefOrGetter<number>,
) {
  const queryClient = useQueryClient()

  function patchThread(patch: Partial<ThreadDetailResponse>) {
    queryClient.setQueryData<ThreadDetailResponse>(
      threadQueryKey(toValue(slug), toValue(threadId)),
      (old) => (old ? { ...old, ...patch } : old),
    )
  }

  async function invalidateCatalog() {
    await queryClient.invalidateQueries({ queryKey: threadsQueryKey(toValue(slug)) })
  }

  async function setLocked(locked: boolean) {
    await setThreadLocked(toValue(slug), toValue(threadId), locked)
    patchThread({ is_locked: locked })
    await invalidateCatalog()
  }

  async function setSticky(sticky: boolean) {
    await setThreadSticky(toValue(slug), toValue(threadId), sticky)
    patchThread({ is_sticky: sticky })
    await invalidateCatalog()
  }

  async function removePost(postNumber: number) {
    await deletePost(toValue(slug), postNumber)
    queryClient.setQueryData<ThreadDetailResponse>(
      threadQueryKey(toValue(slug), toValue(threadId)),
      (old) => {
        if (!old) return old
        const posts = old.posts ?? []
        const removed = posts.find((post) => post.post_number === postNumber)
        if (!removed) return old
        // mirror the server: reply_count tracks non-op replies, so drop it by one
        // unless the deleted post is the op
        const reply_count = removed.is_op ? old.reply_count : Math.max(0, old.reply_count - 1)
        return {
          ...old,
          reply_count,
          posts: posts.filter((post) => post.post_number !== postNumber),
        }
      },
    )
  }

  // admin-only: hard-delete the whole thread, then drop it from the catalog
  // cache and invalidate so every page refetches without it
  async function removeThread() {
    await deleteThread(toValue(slug), toValue(threadId))
    queryClient.setQueryData<ThreadResponse[]>(
      threadsPageQueryKey(toValue(slug), 1),
      (old) => (old ? old.filter((thread) => thread.id !== toValue(threadId)) : old),
    )
    await invalidateCatalog()
  }

  async function ban(postNumber: number, data: BanCreate): Promise<BanResponse> {
    return banPoster(toValue(slug), postNumber, data)
  }

  // the new summary arrives over the thread's ws channel (useThreadWs), same as
  // the automatic beat-triggered run, so this just kicks the job off
  async function generateSummary() {
    await regenerateSummary(toValue(slug), toValue(threadId))
  }

  return { setLocked, setSticky, removePost, removeThread, ban, generateSummary }
}
