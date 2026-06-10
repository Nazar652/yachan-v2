import type { Ref } from 'vue'
import { useQuery } from '@tanstack/vue-query'

import { getPostHistory } from '@/api/posts'

export function postHistoryQueryKey(slug: string | Ref<string>, postNumber: number) {
  return ['post-history', slug, postNumber] as const
}

// fetches a post's pre-edit body lazily — the query only runs once enabled flips
// true (on hover), and the original text never changes once saved, so it stays
// fresh forever.
export function usePostHistory(slug: Ref<string>, postNumber: number, enabled: Ref<boolean>) {
  return useQuery({
    queryKey: postHistoryQueryKey(slug, postNumber),
    queryFn: () => getPostHistory(slug.value, postNumber),
    enabled,
    staleTime: Infinity,
  })
}
