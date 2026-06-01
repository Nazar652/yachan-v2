import { useQuery } from '@tanstack/vue-query'
import type { Ref } from 'vue'
import { getThread } from '@/api/threads'

export function threadQueryKey(slug: string | Ref<string>, id: number | Ref<number>) {
  return ['thread', slug, id] as const
}

export function useThread(slug: Ref<string>, threadId: Ref<number>) {
  return useQuery({
    queryKey: threadQueryKey(slug, threadId),
    queryFn: () => getThread(slug.value, threadId.value),
  })
}

