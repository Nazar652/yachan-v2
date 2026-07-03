import { describe, expect, it, vi } from 'vitest'
import { defineComponent, ref } from 'vue'
import { mount } from '@vue/test-utils'
import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query'

import { useSearch, searchQueryKey } from '@/composables/useSearch'
import { searchPosts } from '@/api/search'

vi.mock('@/api/search', () => ({
  searchPosts: vi.fn(),
}))

function mountWithQuery(setup: () => unknown) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  const Host = defineComponent({
    setup() {
      setup()
      return () => null
    },
  })
  mount(Host, { global: { plugins: [[VueQueryPlugin, { queryClient }]] } })
  return queryClient
}

async function flushQueries() {
  await new Promise((resolve) => setTimeout(resolve, 0))
}

describe('useSearch', () => {
  it('fetches matches into the canonical query key', async () => {
    const results = [
      { board_slug: 'b', thread_id: 1, post_number: 2, is_op: false, name: 'Anon', body: 'cats', body_html: null, created_at: '', score: 0.9 },
    ]
    vi.mocked(searchPosts).mockResolvedValue(results)

    const queryClient = mountWithQuery(() => useSearch(ref('cats'), ref(null)))
    await flushQueries()

    expect(queryClient.getQueryData(searchQueryKey('cats', null))).toBe(results)
    expect(searchPosts).toHaveBeenCalledWith('cats', undefined)
  })

  it('does not fetch when the query is shorter than two characters', async () => {
    vi.mocked(searchPosts).mockReset()
    vi.mocked(searchPosts).mockResolvedValue([])

    mountWithQuery(() => useSearch(ref('a'), ref(null)))
    await flushQueries()

    expect(searchPosts).not.toHaveBeenCalled()
  })
})
