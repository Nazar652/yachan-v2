import { describe, expect, it, vi, beforeEach } from 'vitest'
import { defineComponent } from 'vue'
import { mount } from '@vue/test-utils'
import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query'

import { useCatalogModeration } from '@/composables/useCatalogModeration'
import { threadsQueryKey } from '@/composables/useThreads'
import { setThreadLocked, setThreadSticky } from '@/api/mod'

vi.mock('@/api/mod', () => ({
  setThreadLocked: vi.fn(),
  setThreadSticky: vi.fn(),
}))

const setThreadLockedMock = vi.mocked(setThreadLocked)
const setThreadStickyMock = vi.mocked(setThreadSticky)

beforeEach(() => {
  setThreadLockedMock.mockReset().mockResolvedValue(undefined)
  setThreadStickyMock.mockReset().mockResolvedValue(undefined)
})

function mountModeration(queryClient: QueryClient) {
  let api!: ReturnType<typeof useCatalogModeration>
  const Host = defineComponent({
    setup() {
      api = useCatalogModeration('b')
      return () => null
    },
  })
  mount(Host, { global: { plugins: [[VueQueryPlugin, { queryClient }]] } })
  return api
}

describe('useCatalogModeration', () => {
  it('setLocked calls the api and flips is_locked on the matching thread', async () => {
    const queryClient = new QueryClient()
    queryClient.setQueryData(threadsQueryKey('b'), [
      { id: 1, is_locked: false },
      { id: 2, is_locked: false },
    ])
    const api = mountModeration(queryClient)

    await api.setLocked(2, true)

    expect(setThreadLockedMock).toHaveBeenCalledWith('b', 2, true)
    expect(queryClient.getQueryData(threadsQueryKey('b'))).toEqual([
      { id: 1, is_locked: false },
      { id: 2, is_locked: true },
    ])
  })

  it('setSticky calls the api and flips is_sticky on the matching thread', async () => {
    const queryClient = new QueryClient()
    queryClient.setQueryData(threadsQueryKey('b'), [{ id: 5, is_sticky: false }])
    const api = mountModeration(queryClient)

    await api.setSticky(5, true)

    expect(setThreadStickyMock).toHaveBeenCalledWith('b', 5, true)
    expect(queryClient.getQueryData(threadsQueryKey('b'))).toEqual([{ id: 5, is_sticky: true }])
  })
})
