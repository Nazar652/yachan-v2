import { describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'
import { mount } from '@vue/test-utils'

import BoardListView from '@/views/BoardListView.vue'
import { useBoards } from '@/composables/useBoards'

vi.mock('@/composables/useBoards', () => ({
  useBoards: vi.fn(),
}))

const useBoardsMock = vi.mocked(useBoards)

// the composable returns a tanstack query result; we only need the few
// reactive fields the view reads, so the cast keeps the stub minimal.
function stubBoards(state: Record<string, unknown>) {
  useBoardsMock.mockReturnValue(state as ReturnType<typeof useBoards>)
}

describe('BoardListView', () => {
  it('shows a loading message while pending', () => {
    stubBoards({ data: ref(undefined), isPending: ref(true), isError: ref(false) })
    const wrapper = mount(BoardListView)
    expect(wrapper.text()).toContain('Loading')
  })

  it('shows an error message on failure', () => {
    stubBoards({ data: ref(undefined), isPending: ref(false), isError: ref(true) })
    const wrapper = mount(BoardListView)
    expect(wrapper.text()).toContain('Failed to load boards')
  })

  it('shows an empty state when there are no boards', () => {
    stubBoards({ data: ref([]), isPending: ref(false), isError: ref(false) })
    const wrapper = mount(BoardListView)
    expect(wrapper.text()).toContain('No boards yet')
  })

  it('renders the boards', () => {
    stubBoards({
      data: ref([{ id: 1, slug: 'a', title: 'Anime', description: 'weeb stuff' }]),
      isPending: ref(false),
      isError: ref(false),
    })
    const wrapper = mount(BoardListView)
    expect(wrapper.text()).toContain('/a/')
    expect(wrapper.text()).toContain('Anime')
    expect(wrapper.text()).toContain('weeb stuff')
  })
})
