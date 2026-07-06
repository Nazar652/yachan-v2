import { describe, expect, it, vi } from 'vitest'
import { defineComponent, ref } from 'vue'
import { mount } from '@vue/test-utils'
import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query'

import { useSimilarThreads, similarThreadsQueryKey } from '@/composables/useSimilarThreads'
import { getSimilarThreads } from '@/api/search'

vi.mock('@/api/search', () => ({
  getSimilarThreads: vi.fn(),
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

describe('useSimilarThreads', () => {
  it('fetches similar threads into the canonical query key', async () => {
    const results = [
      {
        board_slug: 'b', thread_id: 2, title: 'other', op_snippet: 'snippet',
        thumbnail_url: null, reply_count: 1, score: 0.7,
      },
    ]
    vi.mocked(getSimilarThreads).mockResolvedValue(results)

    const queryClient = mountWithQuery(() => useSimilarThreads(ref('b'), ref(1)))
    await flushQueries()

    expect(queryClient.getQueryData(similarThreadsQueryKey('b', 1))).toBe(results)
    expect(getSimilarThreads).toHaveBeenCalledWith('b', 1)
  })

  it('does not fetch when threadId is not a valid number', async () => {
    vi.mocked(getSimilarThreads).mockReset()
    vi.mocked(getSimilarThreads).mockResolvedValue([])

    mountWithQuery(() => useSimilarThreads(ref('b'), ref(NaN)))
    await flushQueries()

    expect(getSimilarThreads).not.toHaveBeenCalled()
  })
})
