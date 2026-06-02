import { toValue, type MaybeRefOrGetter } from 'vue'
import { useQueryClient } from '@tanstack/vue-query'

import { threadQueryKey } from '@/composables/useThread'
import { threadsQueryKey } from '@/composables/useThreads'
import { banPoster, deletePost, setThreadLocked, setThreadSticky } from '@/api/mod'
import type { BanCreate, BanResponse, ThreadDetailResponse } from '@/api/types'

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
      (old) =>
        old ? { ...old, posts: (old.posts ?? []).filter((post) => post.post_number !== postNumber) } : old,
    )
  }

  async function ban(postNumber: number, data: BanCreate): Promise<BanResponse> {
    return banPoster(toValue(slug), postNumber, data)
  }

  return { setLocked, setSticky, removePost, ban }
}
