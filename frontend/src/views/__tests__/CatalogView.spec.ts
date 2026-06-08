import { describe, expect, it, vi, beforeEach } from 'vitest'
import { ref } from 'vue'
import { mount, type VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

import CatalogView from '@/views/CatalogView.vue'
import { useThreads } from '@/composables/useThreads'
import { useAuthStore } from '@/stores/auth'

vi.mock('vue-router', () => ({
  useRoute: () => ({ params: { slug: 'b' } }),
  RouterLink: { template: '<a><slot /></a>' },
}))

const globalStubs = { RouterLink: { template: '<a><slot /></a>' } }

vi.mock('@/composables/useThreads', () => ({
  useThreads: vi.fn(),
}))

vi.mock('@/composables/useBoardWs', () => ({
  useBoardWs: vi.fn(),
}))

vi.mock('@/composables/useBoards', () => ({
  useBoards: () => ({ data: ref([{ id: 1, slug: 'b', title: 'Random', description: 'random board' }]) }),
}))

const setLockedMock = vi.fn()
const setStickyMock = vi.fn()
vi.mock('@/composables/useCatalogModeration', () => ({
  useCatalogModeration: () => ({ setLocked: setLockedMock, setSticky: setStickyMock }),
}))

const useThreadsMock = vi.mocked(useThreads)

function stubThreads(state: Record<string, unknown>) {
  useThreadsMock.mockReturnValue(state as ReturnType<typeof useThreads>)
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

  it('shows the board slug and description in the header', () => {
    stubThreads({ data: ref([]), isPending: ref(false), isError: ref(false) })
    const wrapper = mount(CatalogView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('/b/')
    expect(wrapper.text()).toContain('random board')
  })

  it('renders op_post body preview when present', () => {
    stubThreads({
      data: ref([
        {
          id: 5, board_id: 1, title: 'T', is_locked: false, is_sticky: false,
          reply_count: 0, bump_at: '', created_at: '',
          op_post: { body: 'hello preview', thumbnail_url: null },
          last_replies: [],
        },
      ]),
      isPending: ref(false),
      isError: ref(false),
    })
    const wrapper = mount(CatalogView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('hello preview')
  })

  it('shows "Nobody posted anything yet" when last_replies is empty', () => {
    stubThreads({
      data: ref([
        { id: 7, board_id: 1, title: 'T', is_locked: false, is_sticky: false,
          reply_count: 0, bump_at: '', created_at: '', last_replies: [] },
      ]),
      isPending: ref(false),
      isError: ref(false),
    })
    const wrapper = mount(CatalogView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('Nobody posted anything yet')
  })

  it('renders last replies with body and id', () => {
    stubThreads({
      data: ref([
        {
          id: 8, board_id: 1, title: 'T', is_locked: false, is_sticky: false,
          reply_count: 2, bump_at: '', created_at: '',
          last_replies: [
            { id: 100, body: 'first reply', created_at: '2024-01-01T00:00:00' },
            { id: 101, body: 'second reply', created_at: '2024-01-02T00:00:00' },
          ],
        },
      ]),
      isPending: ref(false),
      isError: ref(false),
    })
    const wrapper = mount(CatalogView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('first reply')
    expect(wrapper.text()).toContain('second reply')
    expect(wrapper.text()).toContain('№100')
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

  function stubOneThread() {
    stubThreads({
      data: ref([
        { id: 1, board_id: 1, title: 'T', is_locked: false, is_sticky: false, reply_count: 0, bump_at: '', created_at: '' },
      ]),
      isPending: ref(false),
      isError: ref(false),
    })
  }

  it('hides mod controls when not authenticated', () => {
    stubOneThread()
    const wrapper = mount(CatalogView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).not.toContain('Lock')
    expect(wrapper.text()).not.toContain('Sticky')
  })

  it('shows lock and sticky controls when authenticated', () => {
    useAuthStore().login('jwt', 'admin')
    stubOneThread()
    const wrapper = mount(CatalogView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('Lock')
    expect(wrapper.text()).toContain('Sticky')
  })

  it('toggles a thread lock', async () => {
    useAuthStore().login('jwt', 'admin')
    stubOneThread()
    const wrapper = mount(CatalogView, { global: { stubs: globalStubs } })
    await clickButton(wrapper, 'Lock')
    expect(setLockedMock).toHaveBeenCalledWith(1, true)
  })

  it('toggles a thread sticky', async () => {
    useAuthStore().login('jwt', 'admin')
    stubOneThread()
    const wrapper = mount(CatalogView, { global: { stubs: globalStubs } })
    await clickButton(wrapper, 'Sticky')
    expect(setStickyMock).toHaveBeenCalledWith(1, true)
  })
})

