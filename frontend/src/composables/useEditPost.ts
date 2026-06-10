import { toValue, type MaybeRefOrGetter } from 'vue'
import { useQueryClient } from '@tanstack/vue-query'

import { threadQueryKey } from '@/composables/useThread'
import { editPost as editPostRequest } from '@/api/posts'
import type { PostResponse, ThreadDetailResponse } from '@/api/types'

// edits a post via the api, then replaces it in the thread cache by id so the
// new body and the dropped can_edit flag show immediately. the post_edited
// websocket event reconciles the same post for every other viewer.
export function useEditPost(
  slug: MaybeRefOrGetter<string>,
  threadId: MaybeRefOrGetter<number>,
) {
  const queryClient = useQueryClient()

  async function editPost(postNumber: number, newBody: string | null): Promise<PostResponse> {
    const updated = await editPostRequest(toValue(slug), postNumber, newBody)

    queryClient.setQueryData<ThreadDetailResponse>(
      threadQueryKey(toValue(slug), toValue(threadId)),
      (old) =>
        old
          ? { ...old, posts: (old.posts ?? []).map((post) => (post.id === updated.id ? updated : post)) }
          : old,
    )

    return updated
  }

  return { editPost }
}
