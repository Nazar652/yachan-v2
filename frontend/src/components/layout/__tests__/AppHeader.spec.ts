import { describe, expect, it, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { ref } from 'vue'

import AppHeader from '@/components/layout/AppHeader.vue'
import { useAuthStore } from '@/stores/auth'

vi.mock('@/composables/useBoards', () => ({
  useBoards: () => ({
    data: ref([
      { id: 1, slug: 'b', title: 'Random' },
      { id: 2, slug: 'g', title: 'Games' },
    ]),
  }),
}))

// mutable route stub so each test can place the header on a different page
const routeMock = { name: 'boards', params: {} as Record<string, string>, query: {} as Record<string, string> }
const pushMock = vi.fn()

vi.mock('vue-router', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue-router')>()
  return {
    ...actual,
    useRoute: () => routeMock,
    useRouter: () => ({ push: pushMock }),
    RouterLink: { template: '<a><slot /></a>' },
  }
})

beforeEach(() => {
  localStorage.clear()
  document.documentElement.removeAttribute('data-theme')
  setActivePinia(createPinia())
  routeMock.name = 'boards'
  routeMock.params = {}
  routeMock.query = {}
  pushMock.mockReset()
})

describe('AppHeader', () => {
  it('shows a mod login link when unauthenticated', () => {
    const wrapper = mount(AppHeader)
    expect(wrapper.text()).toContain('Mod login')
  })

  it('shows the mod panel link when authenticated', () => {
    useAuthStore().login('jwt', 'admin')
    const wrapper = mount(AppHeader)
    expect(wrapper.text()).toContain('Mod panel')
  })

  it('shows the ячан wordmark', () => {
    const wrapper = mount(AppHeader)
    expect(wrapper.text()).toContain('ячан')
  })

  it('does not show board tabs on the home page', () => {
    const wrapper = mount(AppHeader)
    // route.name === 'boards' → tabs hidden
    expect(wrapper.find('nav').exists()).toBe(false)
  })

  it('shows board tabs on a board page and highlights the active one', () => {
    routeMock.name = 'catalog'
    routeMock.params = { slug: 'g' }
    const wrapper = mount(AppHeader)
    const tabs = wrapper.find('nav').findAll('a')
    expect(tabs.map((tab) => tab.text())).toEqual(['/b/', '/g/'])
    expect(tabs[1]!.classes()).toContain('bg-gold')
  })

  it('navigates to the search page on submit', async () => {
    const wrapper = mount(AppHeader)
    await wrapper.find('input[type="search"]').setValue('cats')
    await wrapper.find('form').trigger('submit')
    expect(pushMock).toHaveBeenCalledWith({ name: 'search', query: { q: 'cats' } })
  })

  it('does not navigate on an empty search', async () => {
    const wrapper = mount(AppHeader)
    await wrapper.find('form').trigger('submit')
    expect(pushMock).not.toHaveBeenCalled()
  })

  it('toggles the theme from the header button', async () => {
    const wrapper = mount(AppHeader)
    await wrapper.find('button[aria-label="Toggle theme"]').trigger('click')
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
    expect(localStorage.getItem('yachan_theme')).toBe('dark')
  })
})
