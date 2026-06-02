import { describe, expect, it, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

import AppHeader from '@/components/layout/AppHeader.vue'
import { useAuthStore } from '@/stores/auth'

const globalStubs = { RouterLink: { template: '<a><slot /></a>' } }

beforeEach(() => {
  localStorage.clear()
  setActivePinia(createPinia())
})

describe('AppHeader', () => {
  it('shows a mod login link when unauthenticated', () => {
    const wrapper = mount(AppHeader, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('Mod login')
  })

  it('shows the mod panel link when authenticated', () => {
    useAuthStore().login('jwt', 'admin')
    const wrapper = mount(AppHeader, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('Mod panel')
  })
})
