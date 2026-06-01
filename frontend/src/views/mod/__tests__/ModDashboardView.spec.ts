import { describe, expect, it, vi, beforeEach } from 'vitest'
import { ref } from 'vue'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

import ModDashboardView from '@/views/mod/ModDashboardView.vue'
import { useReports } from '@/composables/useReports'
import { resolveReport } from '@/api/mod'
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

vi.mock('@/api/mod', () => ({
  resolveReport: vi.fn(),
}))

const globalStubs = {
  BaseButton: { template: '<button @click="$emit(\'click\')"><slot /></button>', emits: ['click'] },
}

const useReportsMock = vi.mocked(useReports)
const resolveReportMock = vi.mocked(resolveReport)

function stubReports(overrides: Record<string, unknown> = {}) {
  useReportsMock.mockReturnValue({
    data: ref([]),
    isPending: ref(false),
    isError: ref(false),
    ...overrides,
  } as unknown as ReturnType<typeof useReports>)
}

beforeEach(() => {
  localStorage.clear()
  setActivePinia(createPinia())
  pushMock.mockReset()
  invalidateMock.mockReset()
  resolveReportMock.mockReset()
  stubReports()
})

describe('ModDashboardView', () => {
  it('renders the dashboard heading', () => {
    const wrapper = mount(ModDashboardView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('Mod dashboard')
  })

  it('logs out and redirects to the login page', async () => {
    const auth = useAuthStore()
    auth.login('jwt')
    const wrapper = mount(ModDashboardView, { global: { stubs: globalStubs } })

    await wrapper.find('button').trigger('click')

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
    expect(wrapper.text()).toContain('No reports')
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
    // only the logout button remains (no resolve button in the list)
    expect(wrapper.find('ul button').exists()).toBe(false)
  })

  it('resolves a report and invalidates the reports query', async () => {
    stubReports({
      data: ref([{ id: 3, post_id: 9, board_id: 1, reason: 'x', is_resolved: false, created_at: '2024-01-01T00:00:00' }]),
    })
    resolveReportMock.mockResolvedValue(undefined)
    const wrapper = mount(ModDashboardView, { global: { stubs: globalStubs } })

    await wrapper.get('ul button').trigger('click')
    await flushPromises()

    expect(resolveReportMock).toHaveBeenCalledWith(3)
    expect(invalidateMock).toHaveBeenCalledWith({ queryKey: ['reports'] })
  })
})
