import { describe, expect, it, vi, beforeEach } from 'vitest'
import { defineComponent } from 'vue'
import { mount } from '@vue/test-utils'
import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query'

import {
  useThreads,
  threadsPageQueryKey,
  threadsQueryKey,
  THREADS_PAGE_SIZE,
  GALLERY_PAGE_SIZE,
} from '@/composables/useThreads'
import { listThreads } from '@/api/threads'

vi.mock('@/api/threads', () => ({
  listThreads: vi.fn(),
}))

const listThreadsMock = vi.mocked(listThreads)

beforeEach(() => {
  listThreadsMock.mockReset().mockResolvedValue([])
})

function mountThreads(page: number, pageSize?: number) {
  const queryClient = new QueryClient()
  const Host = defineComponent({
    setup() {
      useThreads('b', page, pageSize)
      return () => null
    },
  })
  mount(Host, { global: { plugins: [[VueQueryPlugin, { queryClient }]] } })
  return queryClient
}

describe('threadsPageQueryKey', () => {
  it('defaults to THREADS_PAGE_SIZE when no pageSize is given', () => {
    expect(threadsPageQueryKey('b', 1)).toEqual(['threads', 'b', 1, THREADS_PAGE_SIZE])
  })

  it('includes an explicit pageSize', () => {
    expect(threadsPageQueryKey('b', 2, GALLERY_PAGE_SIZE)).toEqual([
      'threads',
      'b',
      2,
      GALLERY_PAGE_SIZE,
    ])
  })

  it('threadsQueryKey stays a bare prefix', () => {
    expect(threadsQueryKey('b')).toEqual(['threads', 'b'])
  })
})

describe('useThreads', () => {
  it('fetches with THREADS_PAGE_SIZE and keys the cache by the default pageSize', () => {
    mountThreads(1)

    expect(listThreadsMock).toHaveBeenCalledWith('b', THREADS_PAGE_SIZE, 0)
  })

  it('fetches with a custom pageSize and offsets by it', () => {
    mountThreads(2, GALLERY_PAGE_SIZE)

    expect(listThreadsMock).toHaveBeenCalledWith('b', GALLERY_PAGE_SIZE, GALLERY_PAGE_SIZE)
  })

  it('caches list and gallery pages under distinct keys', async () => {
    const queryClient = mountThreads(1, GALLERY_PAGE_SIZE)

    await vi.waitFor(() =>
      expect(queryClient.getQueryData(threadsPageQueryKey('b', 1, GALLERY_PAGE_SIZE))).toEqual([]),
    )
    expect(queryClient.getQueryData(threadsPageQueryKey('b', 1))).toBeUndefined()
  })
})
