import { describe, expect, it, vi } from 'vitest'
import { ref, type Ref } from 'vue'
import { mount } from '@vue/test-utils'

import BoardListView from '@/views/BoardListView.vue'
import { useBoards } from '@/composables/useBoards'
import { useSiteStats } from '@/composables/useSiteStats'
import { useLatestThreads } from '@/composables/useLatestThreads'

vi.mock('@/composables/useBoards', () => ({
  useBoards: vi.fn(),
}))

vi.mock('@/composables/useSiteStats', () => ({
  useSiteStats: vi.fn(() => ({ data: ref(undefined) })),
}))

vi.mock('@/composables/useLatestThreads', () => ({
  useLatestThreads: vi.fn(() => ({ data: ref(undefined) })),
}))

// RouterLink is provided globally by vue-router; stub it so tests run without a router.
const globalStubs = { RouterLink: { template: '<a><slot /></a>' } }

const useBoardsMock = vi.mocked(useBoards)
const useSiteStatsMock = vi.mocked(useSiteStats)
const useLatestThreadsMock = vi.mocked(useLatestThreads)

// the composables return tanstack query results; we only need the few
// reactive fields the view reads, so the cast keeps the stubs minimal.
function stubBoards(state: Record<string, unknown>) {
  useBoardsMock.mockReturnValue(state as ReturnType<typeof useBoards>)
}

function stubStats(data: Ref<unknown>) {
  useSiteStatsMock.mockReturnValue({ data } as ReturnType<typeof useSiteStats>)
}

function stubLatest(data: Ref<unknown>) {
  useLatestThreadsMock.mockReturnValue({ data } as ReturnType<typeof useLatestThreads>)
}

describe('BoardListView', () => {
  it('shows a loading message while pending', () => {
    stubBoards({ data: ref(undefined), isPending: ref(true), isError: ref(false) })
    const wrapper = mount(BoardListView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('Loading')
  })

  it('shows an error message on failure', () => {
    stubBoards({ data: ref(undefined), isPending: ref(false), isError: ref(true) })
    const wrapper = mount(BoardListView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('Failed to load boards')
  })

  it('shows an empty state when there are no boards', () => {
    stubBoards({ data: ref([]), isPending: ref(false), isError: ref(false) })
    const wrapper = mount(BoardListView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('No boards yet')
  })

  it('renders the boards', () => {
    stubBoards({
      data: ref([{ id: 1, slug: 'a', title: 'Anime', description: 'weeb stuff' }]),
      isPending: ref(false),
      isError: ref(false),
    })
    const wrapper = mount(BoardListView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('/a/')
    expect(wrapper.text()).toContain('Anime')
    expect(wrapper.text()).toContain('weeb stuff')
  })

  it('shows an 18+ badge only for nsfw boards', () => {
    stubBoards({
      data: ref([
        { id: 1, slug: 'a', title: 'Anime', description: 'weeb stuff', is_nsfw: false },
        { id: 2, slug: 'nsfw', title: 'Adult', description: null, is_nsfw: true },
      ]),
      isPending: ref(false),
      isError: ref(false),
    })
    const wrapper = mount(BoardListView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('18+')
    const cards = wrapper.findAll('li')
    expect(cards[0]!.text()).not.toContain('18+')
    expect(cards[1]!.text()).toContain('18+')
  })

  it('renders hero stats and per-board counters from the stats endpoint', () => {
    stubBoards({
      data: ref([{ id: 1, slug: 'b', title: 'Random', description: null }]),
      isPending: ref(false),
      isError: ref(false),
    })
    stubStats(
      ref({
        board_count: 4,
        thread_count: 127,
        post_count: 2400,
        online_count: 38,
        boards: [{ slug: 'b', thread_count: 58, post_count: 1340, online_count: 18 }],
      }),
    )
    const wrapper = mount(BoardListView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('boards')
    expect(wrapper.text()).toContain('2.4k')
    expect(wrapper.text()).toContain('38')
    expect(wrapper.text()).toContain('58')
    expect(wrapper.text()).toContain('● 18 online')
  })

  it('renders the latest threads strip', () => {
    stubBoards({ data: ref([]), isPending: ref(false), isError: ref(false) })
    stubLatest(
      ref([
        {
          id: 15,
          board_slug: 'b',
          title: 'First thread',
          reply_count: 10,
          bump_at: '2026-06-10T12:53:00Z',
          created_at: '2026-06-08T20:34:00Z',
          thumbnail_url: '/media/t.jpg',
          last_reply: { id: 15, name: 'Anonymous', body: 'перевірка!!', body_html: null, created_at: '2026-06-10T12:53:00Z' },
        },
        {
          id: 5,
          board_slug: 'g',
          title: null,
          reply_count: 0,
          bump_at: '2026-06-09T09:10:00Z',
          created_at: '2026-06-09T09:10:00Z',
          thumbnail_url: null,
          last_reply: null,
        },
      ]),
    )
    const wrapper = mount(BoardListView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('Latest threads')
    expect(wrapper.text()).toContain('First thread')
    expect(wrapper.text()).toContain('перевірка!!')
    expect(wrapper.text()).toContain('(no title)')
    expect(wrapper.text()).toContain('Nobody posted anything yet')
  })
})
