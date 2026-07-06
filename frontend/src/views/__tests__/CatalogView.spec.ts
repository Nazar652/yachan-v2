import { describe, expect, it, vi, beforeEach } from 'vitest'
import { ref, type Ref } from 'vue'
import { mount, type VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

import CatalogView from '@/views/CatalogView.vue'
import ThreadCard from '@/components/ThreadCard.vue'
import ThreadGalleryCard from '@/components/ThreadGalleryCard.vue'
import { useThreads, THREADS_PAGE_SIZE, GALLERY_PAGE_SIZE } from '@/composables/useThreads'
import { useSiteStats } from '@/composables/useSiteStats'
import { useBoard } from '@/composables/useBoards'
import { useAuthStore } from '@/stores/auth'

const { pushMock, replaceMock, routeMock } = vi.hoisted(() => ({
  pushMock: vi.fn(),
  replaceMock: vi.fn(),
  routeMock: vi.fn(() => ({ params: { slug: 'b' }, query: {} as Record<string, unknown> })),
}))

vi.mock('vue-router', () => ({
  useRoute: () => routeMock(),
  useRouter: () => ({ push: pushMock, replace: replaceMock }),
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
  useBoard: vi.fn(),
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
const useBoardMock = vi.mocked(useBoard)

function stubThreads(state: Record<string, unknown>) {
  useThreadsMock.mockReturnValue(state as ReturnType<typeof useThreads>)
}

function lastThreadsCall() {
  return useThreadsMock.mock.calls[useThreadsMock.mock.calls.length - 1]
}

function stubStats(data: Ref<unknown>) {
  useSiteStatsMock.mockReturnValue({ data } as ReturnType<typeof useSiteStats>)
}

function stubBoard(board: Record<string, unknown>) {
  useBoardMock.mockReturnValue({ data: ref(board) } as ReturnType<typeof useBoard>)
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
  pushMock.mockReset()
  replaceMock.mockReset()
  routeMock.mockReset().mockReturnValue({ params: { slug: 'b' }, query: {} })
  stubBoard({ id: 1, slug: 'b', title: 'Random', description: 'random board', is_nsfw: false })
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

  it('shows an 18+ badge in the banner for nsfw boards', () => {
    stubBoard({ id: 1, slug: 'b', title: 'Random', description: 'random board', is_nsfw: true })
    stubThreads({ data: ref([]), isPending: ref(false), isError: ref(false) })
    const wrapper = mount(CatalogView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('18+')
  })

  it('hides the 18+ badge for sfw boards', () => {
    stubThreads({ data: ref([]), isPending: ref(false), isError: ref(false) })
    const wrapper = mount(CatalogView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).not.toContain('18+')
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

  it('defaults to the list view when neither the url nor localStorage say otherwise', () => {
    stubThreads({ data: ref([]), isPending: ref(false), isError: ref(false) })
    mount(CatalogView, { global: { stubs: globalStubs } })
    expect(lastThreadsCall()?.[2]).toMatchObject({ value: THREADS_PAGE_SIZE })
  })

  it('reads the initial view from the url query over localStorage', () => {
    routeMock.mockReturnValue({ params: { slug: 'b' }, query: { view: 'gallery' } })
    localStorage.setItem('yachan_catalog_view', 'list')
    stubThreads({ data: ref([]), isPending: ref(false), isError: ref(false) })
    mount(CatalogView, { global: { stubs: globalStubs } })
    expect(lastThreadsCall()?.[2]).toMatchObject({ value: GALLERY_PAGE_SIZE })
  })

  it('falls back to the stored view when the url has none', () => {
    localStorage.setItem('yachan_catalog_view', 'gallery')
    stubThreads({ data: ref([]), isPending: ref(false), isError: ref(false) })
    mount(CatalogView, { global: { stubs: globalStubs } })
    expect(lastThreadsCall()?.[2]).toMatchObject({ value: GALLERY_PAGE_SIZE })
  })

  it('switching to gallery updates the query, localStorage and pageSize', async () => {
    stubThreads({ data: ref([]), isPending: ref(false), isError: ref(false) })
    const wrapper = mount(CatalogView, { global: { stubs: globalStubs } })

    await clickButton(wrapper, 'Gallery')

    expect(replaceMock).toHaveBeenCalledWith({ query: { view: 'gallery' } })
    expect(localStorage.getItem('yachan_catalog_view')).toBe('gallery')
    expect(lastThreadsCall()?.[2]).toMatchObject({ value: GALLERY_PAGE_SIZE })
  })

  it('resets the page to 1 when switching view mode', async () => {
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

    await clickButton(wrapper, 'Next ›')
    expect(lastThreadsCall()?.[1]).toMatchObject({ value: 2 })

    await clickButton(wrapper, 'Gallery')
    expect(lastThreadsCall()?.[1]).toMatchObject({ value: 1 })
  })

  it('renders gallery tiles instead of list cards in gallery mode', async () => {
    stubThreads({
      data: ref([makeThread({ id: 1, title: 'Hello world' })]),
      isPending: ref(false),
      isError: ref(false),
    })
    const wrapper = mount(CatalogView, { global: { stubs: globalStubs } })

    await clickButton(wrapper, 'Gallery')

    expect(wrapper.findComponent(ThreadCard).exists()).toBe(false)
    expect(wrapper.findComponent(ThreadGalleryCard).exists()).toBe(true)
    expect(wrapper.text()).toContain('Hello world')
  })
})
