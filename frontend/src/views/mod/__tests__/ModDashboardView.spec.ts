import { describe, expect, it, vi, beforeEach } from 'vitest'
import { ref } from 'vue'
import { mount, flushPromises, type VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

import ModDashboardView from '@/views/mod/ModDashboardView.vue'
import { useReports } from '@/composables/useReports'
import { useBoards } from '@/composables/useBoards'
import { resolveReport, createBoard, updateBoard } from '@/api/mod'
import { useAuthStore } from '@/stores/auth'

const pushMock = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({ push: pushMock }),
}))

const invalidateMock = vi.fn()
vi.mock('@tanstack/vue-query', () => ({
  useQueryClient: () => ({ invalidateQueries: invalidateMock }),
}))

vi.mock('@/composables/useReports', () => ({
  useReports: vi.fn(),
  reportsQueryKey: ['reports'],
}))

vi.mock('@/composables/useBoards', () => ({
  useBoards: vi.fn(),
  boardsQueryKey: ['boards'],
}))

vi.mock('@/api/mod', () => ({
  resolveReport: vi.fn(),
  createBoard: vi.fn(),
  updateBoard: vi.fn(),
}))

// mock the composable but keep the real moveItem (the drop handler uses it)
const reorderMock = vi.hoisted(() => vi.fn())
vi.mock('@/composables/useBoardReorder', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/composables/useBoardReorder')>()),
  useBoardReorder: () => ({ reorder: reorderMock }),
}))

const globalStubs = {
  BaseButton: { template: '<button @click="$emit(\'click\')"><slot /></button>', emits: ['click'] },
  BaseInput: {
    template: '<input @input="$emit(\'update:modelValue\', $event.target.value)" />',
    props: ['modelValue', 'type'],
    emits: ['update:modelValue'],
  },
}

const useReportsMock = vi.mocked(useReports)
const useBoardsMock = vi.mocked(useBoards)
const resolveReportMock = vi.mocked(resolveReport)
const createBoardMock = vi.mocked(createBoard)
const updateBoardMock = vi.mocked(updateBoard)

function stubReports(overrides: Record<string, unknown> = {}) {
  useReportsMock.mockReturnValue({
    data: ref([]),
    isPending: ref(false),
    isError: ref(false),
    ...overrides,
  } as unknown as ReturnType<typeof useReports>)
}

function stubBoards(boards: unknown[] = []) {
  useBoardsMock.mockReturnValue({
    data: ref(boards),
    isPending: ref(false),
    isError: ref(false),
  } as unknown as ReturnType<typeof useBoards>)
}

function clickButton(wrapper: VueWrapper, label: string) {
  const button = wrapper.findAll('button').find((candidate) => candidate.text() === label)
  if (!button) throw new Error(`button "${label}" not found`)
  return button.trigger('click')
}

function board(overrides: Record<string, unknown> = {}) {
  return { id: 1, slug: 'a', title: 'Anime', description: 'desc', bump_limit: 300, is_active: true, position: 0, created_at: '', ...overrides }
}

beforeEach(() => {
  localStorage.clear()
  setActivePinia(createPinia())
  pushMock.mockReset()
  invalidateMock.mockReset()
  resolveReportMock.mockReset()
  createBoardMock.mockReset()
  updateBoardMock.mockReset()
  reorderMock.mockReset()
  stubReports()
  stubBoards()
})

describe('ModDashboardView', () => {
  it('renders the dashboard heading', () => {
    const wrapper = mount(ModDashboardView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('Mod dashboard')
  })

  it('logs out and redirects to the login page', async () => {
    const auth = useAuthStore()
    auth.login('jwt', 'admin')
    const wrapper = mount(ModDashboardView, { global: { stubs: globalStubs } })

    await clickButton(wrapper, 'Log out')

    expect(auth.isAuthenticated).toBe(false)
    expect(pushMock).toHaveBeenCalledWith('/mod/login')
  })

  it('shows a loading state while pending', () => {
    stubReports({ data: ref(undefined), isPending: ref(true) })
    const wrapper = mount(ModDashboardView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('Loading')
  })

  it('shows an error state on failure', () => {
    stubReports({ data: ref(undefined), isError: ref(true) })
    const wrapper = mount(ModDashboardView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('Failed to load reports')
  })

  it('shows an empty state when there are no reports', () => {
    stubReports({ data: ref([]) })
    const wrapper = mount(ModDashboardView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('No open reports. The fields are calm.')
  })

  it('renders a report row with its reason and post id', () => {
    stubReports({
      data: ref([{ id: 1, post_id: 42, board_id: 1, reason: 'spam', is_resolved: false, created_at: '2024-01-01T00:00:00' }]),
    })
    const wrapper = mount(ModDashboardView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('post 42')
    expect(wrapper.text()).toContain('spam')
  })

  it('shows a resolved label instead of a button for resolved reports', () => {
    stubReports({
      data: ref([{ id: 1, post_id: 42, board_id: 1, reason: 'spam', is_resolved: true, created_at: '2024-01-01T00:00:00' }]),
    })
    const wrapper = mount(ModDashboardView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('resolved')
    expect(wrapper.find('ul button').exists()).toBe(false)
  })

  it('resolves a report and invalidates the reports query', async () => {
    stubReports({
      data: ref([{ id: 3, post_id: 9, board_id: 1, reason: 'x', is_resolved: false, created_at: '2024-01-01T00:00:00' }]),
    })
    resolveReportMock.mockResolvedValue(undefined)
    const wrapper = mount(ModDashboardView, { global: { stubs: globalStubs } })

    await clickButton(wrapper, 'Resolve')
    await flushPromises()

    expect(resolveReportMock).toHaveBeenCalledWith(3)
    expect(invalidateMock).toHaveBeenCalledWith({ queryKey: ['reports'] })
  })

  it('hides board management for a moderator', () => {
    useAuthStore().login('jwt', 'moderator')
    stubBoards([board()])
    const wrapper = mount(ModDashboardView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).not.toContain('Boards')
    expect(wrapper.text()).not.toContain('Create board')
  })

  it('shows board management and lists boards for an admin', () => {
    useAuthStore().login('jwt', 'admin')
    stubBoards([board({ slug: 'a', title: 'Anime' })])
    const wrapper = mount(ModDashboardView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('Boards')
    expect(wrapper.text()).toContain('/a/')
    expect(wrapper.text()).toContain('Anime')
  })

  it('shows the board description in the list row', () => {
    useAuthStore().login('jwt', 'admin')
    stubBoards([board({ slug: 'a', title: 'Anime', description: 'Anime & manga' })])
    const wrapper = mount(ModDashboardView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('Anime & manga')
  })

  it('reorders boards via drag and drop and persists the new order', async () => {
    useAuthStore().login('jwt', 'admin')
    reorderMock.mockResolvedValue(undefined)
    stubBoards([
      board({ id: 1, slug: 'a', title: 'A' }),
      board({ id: 2, slug: 'b', title: 'B' }),
      board({ id: 3, slug: 'c', title: 'C' }),
    ])
    const wrapper = mount(ModDashboardView, { global: { stubs: globalStubs } })

    const rows = wrapper.findAll('section li')
    const [source, , target] = rows
    if (!source || !target) throw new Error('expected three board rows')
    await source.trigger('dragstart')
    await target.trigger('drop')
    await flushPromises()

    expect(reorderMock).toHaveBeenCalledWith(['b', 'c', 'a'])
  })

  it('creates a board and invalidates the boards query', async () => {
    useAuthStore().login('jwt', 'admin')
    createBoardMock.mockResolvedValue(board() as never)
    const wrapper = mount(ModDashboardView, { global: { stubs: globalStubs } })

    await wrapper.find('#board-slug').setValue('b')
    await wrapper.find('#board-title').setValue('Random')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(createBoardMock).toHaveBeenCalledWith({
      slug: 'b',
      title: 'Random',
      description: null,
      bump_limit: 300,
    })
    expect(invalidateMock).toHaveBeenCalledWith({ queryKey: ['boards'] })
  })

  it('edits a board and invalidates the boards query', async () => {
    useAuthStore().login('jwt', 'admin')
    stubBoards([board({ slug: 'a', title: 'Anime', description: 'desc' })])
    updateBoardMock.mockResolvedValue(board() as never)
    const wrapper = mount(ModDashboardView, { global: { stubs: globalStubs } })

    await clickButton(wrapper, 'Edit')
    await wrapper.find('#edit-title').setValue('New title')
    await clickButton(wrapper, 'Save')
    await flushPromises()

    expect(updateBoardMock).toHaveBeenCalledWith('a', {
      title: 'New title',
      description: 'desc',
      bump_limit: 300,
      is_active: true,
    })
    expect(invalidateMock).toHaveBeenCalledWith({ queryKey: ['boards'] })
  })
})
