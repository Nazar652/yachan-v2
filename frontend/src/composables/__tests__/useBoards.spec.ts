import { describe, expect, it, vi, beforeEach } from 'vitest'
import { defineComponent, ref, type Ref } from 'vue'
import { mount, flushPromises } from '@vue/test-utils'
import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query'

import { useBoard, useBoards, boardQueryKey, boardsQueryKey } from '@/composables/useBoards'
import { getBoard, listBoards } from '@/api/boards'

vi.mock('@/api/boards', () => ({
  getBoard: vi.fn(),
  listBoards: vi.fn(),
}))

const getBoardMock = vi.mocked(getBoard)
const listBoardsMock = vi.mocked(listBoards)

function mountHost(setup: () => void) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const Host = defineComponent({
    setup() {
      setup()
      return () => null
    },
  })
  mount(Host, { global: { plugins: [[VueQueryPlugin, { queryClient }]] } })
  return queryClient
}

describe('useBoards', () => {
  beforeEach(() => listBoardsMock.mockReset())

  it('fetches the board list and caches it under the list key', async () => {
    const boards = [{ id: 1, slug: 'b', title: 'Random' }]
    listBoardsMock.mockResolvedValue(boards as never)
    const queryClient = mountHost(() => useBoards())

    await flushPromises()

    expect(queryClient.getQueryData(boardsQueryKey)).toBe(boards)
  })
})

describe('useBoard', () => {
  beforeEach(() => getBoardMock.mockReset())

  it('fetches a single board and caches it under the slug key', async () => {
    const board = { id: 1, slug: 'b', title: 'Random' }
    getBoardMock.mockResolvedValue(board as never)
    const queryClient = mountHost(() => useBoard('b'))

    await flushPromises()

    expect(getBoardMock).toHaveBeenCalledWith('b')
    expect(queryClient.getQueryData(boardQueryKey('b'))).toBe(board)
  })

  it('refetches under the new key when the slug changes', async () => {
    getBoardMock.mockResolvedValue({ id: 2, slug: 'g', title: 'Tech' } as never)
    const slug: Ref<string> = ref('b')
    const queryClient = mountHost(() => useBoard(slug))
    await flushPromises()

    slug.value = 'g'
    await flushPromises()

    expect(getBoardMock).toHaveBeenLastCalledWith('g')
    expect(queryClient.getQueryData(boardQueryKey('g'))).toEqual({ id: 2, slug: 'g', title: 'Tech' })
  })
})
