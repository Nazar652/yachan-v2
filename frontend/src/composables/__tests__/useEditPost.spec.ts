import { describe, expect, it, vi, beforeEach } from 'vitest'
import { defineComponent } from 'vue'
import { mount } from '@vue/test-utils'
import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query'

import { useEditPost } from '@/composables/useEditPost'
import { threadQueryKey } from '@/composables/useThread'
import { editPost } from '@/api/posts'

vi.mock('@/api/posts', () => ({
  editPost: vi.fn(),
}))

const editPostMock = vi.mocked(editPost)

beforeEach(() => editPostMock.mockReset())

function mountEditPost(queryClient: QueryClient) {
  let api!: ReturnType<typeof useEditPost>
  const Host = defineComponent({
    setup() {
      api = useEditPost('b', 42)
      return () => null
    },
  })
  mount(Host, { global: { plugins: [[VueQueryPlugin, { queryClient }]] } })
  return api
}

describe('useEditPost', () => {
  it('calls the api and replaces the post in the thread cache by id', async () => {
    const updated = { id: 2, post_number: 5, body: 'new', is_edited: true, can_edit: false }
    editPostMock.mockResolvedValue(updated as never)

    const queryClient = new QueryClient()
    queryClient.setQueryData(threadQueryKey('b', 42), {
      id: 42,
      posts: [{ id: 1, post_number: 1 }, { id: 2, post_number: 5, body: 'old', can_edit: true }],
    })
    const api = mountEditPost(queryClient)

    await expect(api.editPost(5, 'new')).resolves.toBe(updated)

    expect(editPostMock).toHaveBeenCalledWith('b', 5, 'new')
    expect(queryClient.getQueryData(threadQueryKey('b', 42))).toEqual({
      id: 42,
      posts: [{ id: 1, post_number: 1 }, updated],
    })
  })

  it('leaves the cache untouched when the thread is not cached', async () => {
    const updated = { id: 2, post_number: 5, is_edited: true }
    editPostMock.mockResolvedValue(updated as never)

    const queryClient = new QueryClient()
    const api = mountEditPost(queryClient)

    await api.editPost(5, 'new')

    expect(queryClient.getQueryData(threadQueryKey('b', 42))).toBeUndefined()
  })
})
