import { describe, expect, it, vi, beforeEach } from 'vitest'
import { defineComponent } from 'vue'
import { mount } from '@vue/test-utils'
import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query'

import { useBoardReorder, moveItem } from '@/composables/useBoardReorder'
import { boardsQueryKey } from '@/composables/useBoards'
import { reorderBoards } from '@/api/mod'

vi.mock('@/api/mod', () => ({ reorderBoards: vi.fn() }))

const reorderBoardsMock = vi.mocked(reorderBoards)

beforeEach(() => {
  reorderBoardsMock.mockReset().mockResolvedValue([])
})

function mountReorder(queryClient: QueryClient) {
  let api!: ReturnType<typeof useBoardReorder>
  const Host = defineComponent({
    setup() {
      api = useBoardReorder()
      return () => null
    },
  })
  mount(Host, { global: { plugins: [[VueQueryPlugin, { queryClient }]] } })
  return api
}

describe('moveItem', () => {
  it('moves an item forward', () => {
    expect(moveItem(['a', 'b', 'c'], 0, 2)).toEqual(['b', 'c', 'a'])
  })

  it('moves an item backward', () => {
    expect(moveItem(['a', 'b', 'c'], 2, 0)).toEqual(['c', 'a', 'b'])
  })

  it('does not mutate the input array', () => {
    const input = ['a', 'b', 'c']
    moveItem(input, 0, 1)
    expect(input).toEqual(['a', 'b', 'c'])
  })
})

describe('useBoardReorder', () => {
  it('reorder calls the api and invalidates the boards query', async () => {
    const queryClient = new QueryClient()
    const invalidate = vi.spyOn(queryClient, 'invalidateQueries')
    const api = mountReorder(queryClient)

    await api.reorder(['g', 'b', 't'])

    expect(reorderBoardsMock).toHaveBeenCalledWith(['g', 'b', 't'])
    expect(invalidate).toHaveBeenCalledWith({ queryKey: boardsQueryKey })
  })
})
