import { describe, expect, it, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { ref } from 'vue'

import AppHeader from '@/components/layout/AppHeader.vue'
import { useAuthStore } from '@/stores/auth'

vi.mock('@/composables/useBoards', () => ({
  useBoards: () => ({ data: ref([{ id: 1, slug: 'b', title: 'Random' }]) }),
}))

// provide a minimal route stub so useRoute() doesn't throw
vi.mock('vue-router', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue-router')>()
  return {
    ...actual,
    useRoute: () => ({ name: 'boards', params: {} }),
    RouterLink: { template: '<a><slot /></a>' },
  }
})

beforeEach(() => {
  localStorage.clear()
  setActivePinia(createPinia())
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

  it('shows yachan logo link', () => {
    const wrapper = mount(AppHeader)
    expect(wrapper.text()).toContain('yachan')
  })

  it('does not show board tabs on the home page', () => {
    const wrapper = mount(AppHeader)
    // route.name === 'boards' → tabs hidden
    expect(wrapper.find('nav').exists()).toBe(false)
  })
})
