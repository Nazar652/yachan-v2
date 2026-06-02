import { toValue, type MaybeRefOrGetter } from 'vue'
import { useQueryClient } from '@tanstack/vue-query'

import { threadsQueryKey } from '@/composables/useThreads'
import { setThreadLocked, setThreadSticky } from '@/api/mod'
import type { ThreadResponse } from '@/api/types'

// lock/sticky from the catalog. unlike useModeration (which patches one thread's
// detail cache), this flips the flag on the matching item in the threads-list
// cache so the card icon updates without a refetch.
export function useCatalogModeration(slug: MaybeRefOrGetter<string>) {
  const queryClient = useQueryClient()

  function patchThread(threadId: number, patch: Partial<ThreadResponse>) {
    queryClient.setQueryData<ThreadResponse[]>(threadsQueryKey(toValue(slug)), (old) =>
      old ? old.map((thread) => (thread.id === threadId ? { ...thread, ...patch } : thread)) : old,
    )
  }

  async function setLocked(threadId: number, locked: boolean) {
    await setThreadLocked(toValue(slug), threadId, locked)
    patchThread(threadId, { is_locked: locked })
  }

  async function setSticky(threadId: number, sticky: boolean) {
    await setThreadSticky(toValue(slug), threadId, sticky)
    patchThread(threadId, { is_sticky: sticky })
  }

  return { setLocked, setSticky }
}
