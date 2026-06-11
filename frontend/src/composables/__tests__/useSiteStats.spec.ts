import { describe, expect, it, vi } from 'vitest'
import { defineComponent } from 'vue'
import { mount } from '@vue/test-utils'
import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query'

import { useSiteStats, siteStatsQueryKey } from '@/composables/useSiteStats'
import { useLatestThreads, latestThreadsQueryKey } from '@/composables/useLatestThreads'
import { fetchSiteStats } from '@/api/stats'
import { listLatestThreads } from '@/api/threads'

vi.mock('@/api/stats', () => ({
  fetchSiteStats: vi.fn(),
}))

vi.mock('@/api/threads', () => ({
  listLatestThreads: vi.fn(),
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

describe('useSiteStats', () => {
  it('fetches the stats into the canonical query key', async () => {
    const stats = { board_count: 4, thread_count: 127, post_count: 2400, online_count: 38, boards: [] }
    vi.mocked(fetchSiteStats).mockResolvedValue(stats)

    const queryClient = mountWithQuery(() => useSiteStats())
    await flushQueries()

    expect(queryClient.getQueryData(siteStatsQueryKey)).toBe(stats)
  })
})

describe('useLatestThreads', () => {
  it('fetches the latest threads into the canonical query key', async () => {
    const latest = [{ id: 1, board_slug: 'b', title: null, reply_count: 0, bump_at: '', created_at: '' }]
    vi.mocked(listLatestThreads).mockResolvedValue(latest)

    const queryClient = mountWithQuery(() => useLatestThreads())
    await flushQueries()

    expect(queryClient.getQueryData(latestThreadsQueryKey)).toBe(latest)
  })
})
