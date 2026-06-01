import { describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'
import { mount } from '@vue/test-utils'

import CatalogView from '@/views/CatalogView.vue'
import { useThreads } from '@/composables/useThreads'

vi.mock('vue-router', () => ({
  useRoute: () => ({ params: { slug: 'b' } }),
}))

const globalStubs = { RouterLink: { template: '<a><slot /></a>' } }

vi.mock('@/composables/useThreads', () => ({
  useThreads: vi.fn(),
}))

const useThreadsMock = vi.mocked(useThreads)

function stubThreads(state: Record<string, unknown>) {
  useThreadsMock.mockReturnValue(state as ReturnType<typeof useThreads>)
}

describe('CatalogView', () => {
  it('shows a loading message while pending', () => {
    stubThreads({ data: ref(undefined), isPending: ref(true), isError: ref(false) })
    const wrapper = mount(CatalogView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('Loading')
  })

  it('shows an error message on failure', () => {
    stubThreads({ data: ref(undefined), isPending: ref(false), isError: ref(true) })
    const wrapper = mount(CatalogView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('Failed to load threads')
  })

  it('shows an empty state when there are no threads', () => {
    stubThreads({ data: ref([]), isPending: ref(false), isError: ref(false) })
    const wrapper = mount(CatalogView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('No threads yet')
  })

  it('renders thread cards with title and reply count', () => {
    stubThreads({
      data: ref([
        { id: 1, board_id: 1, title: 'Hello world', is_locked: false, is_sticky: false, reply_count: 5, bump_at: '', created_at: '' },
      ]),
      isPending: ref(false),
      isError: ref(false),
    })
    const wrapper = mount(CatalogView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('Hello world')
    expect(wrapper.text()).toContain('5 replies')
  })

  it('shows (no title) when thread title is null', () => {
    stubThreads({
      data: ref([
        { id: 2, board_id: 1, title: null, is_locked: false, is_sticky: false, reply_count: 0, bump_at: '', created_at: '' },
      ]),
      isPending: ref(false),
      isError: ref(false),
    })
    const wrapper = mount(CatalogView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('(no title)')
  })

  it('shows the board slug in the header', () => {
    stubThreads({ data: ref([]), isPending: ref(false), isError: ref(false) })
    const wrapper = mount(CatalogView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('/b/')
  })

  it('shows sticky and locked icons', () => {
    stubThreads({
      data: ref([
        { id: 3, board_id: 1, title: 'Pinned', is_locked: true, is_sticky: true, reply_count: 1, bump_at: '', created_at: '' },
      ]),
      isPending: ref(false),
      isError: ref(false),
    })
    const wrapper = mount(CatalogView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('📌')
    expect(wrapper.text()).toContain('🔒')
  })
})

