import { describe, expect, it, vi, beforeEach } from 'vitest'
import { defineComponent, ref, type Ref } from 'vue'
import { mount, flushPromises } from '@vue/test-utils'
import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query'

import { useReports, reportsQueryKey } from '@/composables/useReports'
import { listReports } from '@/api/mod'

vi.mock('@/api/mod', () => ({
  listReports: vi.fn(),
}))

const listReportsMock = vi.mocked(listReports)

function mountReports(boardId: Ref<number | null>) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const Host = defineComponent({
    setup() {
      useReports(boardId)
      return () => null
    },
  })
  mount(Host, { global: { plugins: [[VueQueryPlugin, { queryClient }]] } })
  return queryClient
}

describe('useReports', () => {
  beforeEach(() => listReportsMock.mockReset())

  it('fetches all reports and caches them under the unfiltered key', async () => {
    const reports = [{ id: 1, post_id: 5, board_id: 1, reason: 'spam', is_resolved: false, created_at: '' }]
    listReportsMock.mockResolvedValue(reports as never)
    const queryClient = mountReports(ref(null))

    await flushPromises()

    expect(listReportsMock).toHaveBeenCalledWith(null)
    expect(queryClient.getQueryData([...reportsQueryKey, null])).toBe(reports)
  })

  it('refetches under the filtered key when the board filter changes', async () => {
    listReportsMock.mockResolvedValue([])
    const boardId = ref<number | null>(null)
    const queryClient = mountReports(boardId)
    await flushPromises()

    boardId.value = 3
    await flushPromises()

    expect(listReportsMock).toHaveBeenLastCalledWith(3)
    expect(queryClient.getQueryData([...reportsQueryKey, 3])).toEqual([])
  })
})
