import { describe, expect, it, vi, beforeEach } from 'vitest'
import { ref, type Ref } from 'vue'
import { mount, type VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

import CatalogView from '@/views/CatalogView.vue'
import { useThreads } from '@/composables/useThreads'
import { useSiteStats } from '@/composables/useSiteStats'
import { useAuthStore } from '@/stores/auth'

vi.mock('vue-router', () => ({
  useRoute: () => ({ params: { slug: 'b' } }),
  RouterLink: { template: '<a><slot /></a>' },
}))

const globalStubs = { RouterLink: { template: '<a><slot /></a>' } }

// keep THREADS_PAGE_SIZE and the key helpers real; stub only the query composable
vi.mock('@/composables/useThreads', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/composables/useThreads')>()
  return { ...actual, useThreads: vi.fn() }
})

vi.mock('@/composables/useBoardWs', () => ({
  useBoardWs: vi.fn(),
}))

vi.mock('@/composables/useBoards', () => ({
  useBoards: () => ({ data: ref([{ id: 1, slug: 'b', title: 'Random', description: 'random board' }]) }),
}))

vi.mock('@/composables/useSiteStats', () => ({
  useSiteStats: vi.fn(() => ({ data: ref(undefined) })),
}))

const setLockedMock = vi.fn()
const setStickyMock = vi.fn()
vi.mock('@/composables/useCatalogModeration', () => ({
  useCatalogModeration: () => ({ setLocked: setLockedMock, setSticky: setStickyMock }),
}))

const useThreadsMock = vi.mocked(useThreads)
const useSiteStatsMock = vi.mocked(useSiteStats)

function stubThreads(state: Record<string, unknown>) {
  useThreadsMock.mockReturnValue(state as ReturnType<typeof useThreads>)
}

function stubStats(data: Ref<unknown>) {
  useSiteStatsMock.mockReturnValue({ data } as ReturnType<typeof useSiteStats>)
}

function makeThread(overrides: Record<string, unknown> = {}) {
  return {
    id: 1,
    board_id: 1,
    title: 'Hello world',
    is_locked: false,
    is_sticky: false,
    reply_count: 5,
    bump_at: '2026-06-10T12:00:00Z',
    created_at: '2026-06-08T12:00:00Z',
    last_replies: [],
    ...overrides,
  }
}

// click a button by its visible label (each card renders several buttons)
function clickButton(wrapper: VueWrapper, label: string) {
  const button = wrapper.findAll('button').find((candidate) => candidate.text() === label)
  if (!button) throw new Error(`button "${label}" not found`)
  return button.trigger('click')
}

beforeEach(() => {
  localStorage.clear()
  setActivePinia(createPinia())
  setLockedMock.mockReset()
  setStickyMock.mockReset()
})

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
    stubThreads({ data: ref([makeThread()]), isPending: ref(false), isError: ref(false) })
    const wrapper = mount(CatalogView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('Hello world')
    expect(wrapper.text()).toContain('5 replies')
  })

  it('shows the board banner with slug, description and stats', () => {
    stubThreads({ data: ref([]), isPending: ref(false), isError: ref(false) })
    stubStats(
      ref({
        board_count: 1,
        thread_count: 58,
        post_count: 1340,
        online_count: 18,
        boards: [{ slug: 'b', thread_count: 58, post_count: 1340, online_count: 18 }],
      }),
    )
    const wrapper = mount(CatalogView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('/b/')
    expect(wrapper.text()).toContain('random board')
    expect(wrapper.text()).toContain('58')
    expect(wrapper.text()).toContain('● 18 online now')
  })

  it('renders the pager when the board has more than one page', () => {
    stubThreads({ data: ref([makeThread()]), isPending: ref(false), isError: ref(false) })
    stubStats(
      ref({
        board_count: 1,
        thread_count: 35,
        post_count: 100,
        online_count: 1,
        boards: [{ slug: 'b', thread_count: 35, post_count: 100, online_count: 1 }],
      }),
    )
    const wrapper = mount(CatalogView, { global: { stubs: globalStubs } })
    // 35 threads / 10 per page -> 4 pages
    expect(wrapper.find('nav').exists()).toBe(true)
    expect(wrapper.text()).toContain('Next')
  })

  it('reorders the page by reply count when the sort changes', async () => {
    stubThreads({
      data: ref([
        makeThread({ id: 1, title: 'few', reply_count: 1 }),
        makeThread({ id: 2, title: 'many', reply_count: 9 }),
      ]),
      isPending: ref(false),
      isError: ref(false),
    })
    const wrapper = mount(CatalogView, { global: { stubs: globalStubs } })
    await clickButton(wrapper, 'Most replies')
    const text = wrapper.text()
    expect(text.indexOf('many')).toBeLessThan(text.indexOf('few'))
  })

  it('hides mod controls for anonymous visitors', () => {
    stubThreads({ data: ref([makeThread()]), isPending: ref(false), isError: ref(false) })
    const wrapper = mount(CatalogView, { global: { stubs: globalStubs } })
    expect(wrapper.findAll('button').some((button) => button.text() === 'Lock')).toBe(false)
  })

  it('locks a thread from the card mod bar', async () => {
    useAuthStore().login('jwt', 'admin')
    stubThreads({ data: ref([makeThread()]), isPending: ref(false), isError: ref(false) })
    const wrapper = mount(CatalogView, { global: { stubs: globalStubs } })
    await clickButton(wrapper, 'Lock')
    expect(setLockedMock).toHaveBeenCalledWith(1, true)
  })

  it('stickies a thread from the card mod bar', async () => {
    useAuthStore().login('jwt', 'admin')
    stubThreads({ data: ref([makeThread()]), isPending: ref(false), isError: ref(false) })
    const wrapper = mount(CatalogView, { global: { stubs: globalStubs } })
    await clickButton(wrapper, 'Sticky')
    expect(setStickyMock).toHaveBeenCalledWith(1, true)
  })
})
