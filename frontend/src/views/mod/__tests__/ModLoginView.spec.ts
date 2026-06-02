import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

import ModLoginView from '@/views/mod/ModLoginView.vue'
import { modLogin } from '@/api/mod'
import { useAuthStore } from '@/stores/auth'

const pushMock = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({ push: pushMock }),
}))

vi.mock('@/api/mod', () => ({
  modLogin: vi.fn(),
}))

const globalStubs = {
  BaseButton: { template: '<button :type="type" @click="$emit(\'click\')"><slot /></button>', props: ['type'], emits: ['click'] },
  BaseInput: {
    template: '<input @input="$emit(\'update:modelValue\', $event.target.value)" />',
    props: ['modelValue', 'type'],
    emits: ['update:modelValue'],
  },
}

const modLoginMock = vi.mocked(modLogin)

beforeEach(() => {
  localStorage.clear()
  setActivePinia(createPinia())
  pushMock.mockReset()
  modLoginMock.mockReset()
})

describe('ModLoginView', () => {
  it('renders the login heading', () => {
    const wrapper = mount(ModLoginView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('Mod login')
  })

  it('shows a validation error and does not submit when fields are empty', async () => {
    const wrapper = mount(ModLoginView, { global: { stubs: globalStubs } })
    await wrapper.find('form').trigger('submit')
    expect(wrapper.text()).toContain('Enter username and password')
    expect(modLoginMock).not.toHaveBeenCalled()
  })

  it('logs in, stores the token and role, and redirects on success', async () => {
    modLoginMock.mockResolvedValue({ access_token: 'jwt-9', token_type: 'bearer', role: 'admin' })
    const wrapper = mount(ModLoginView, { global: { stubs: globalStubs } })

    await wrapper.find('#mod-username').setValue('admin')
    await wrapper.find('#mod-password').setValue('secret')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(modLoginMock).toHaveBeenCalledWith('admin', 'secret')
    const auth = useAuthStore()
    expect(auth.token).toBe('jwt-9')
    expect(auth.role).toBe('admin')
    expect(pushMock).toHaveBeenCalledWith('/mod')
  })

  it('shows an error message when login fails', async () => {
    modLoginMock.mockRejectedValue({ detail: 'bad credentials' })
    const wrapper = mount(ModLoginView, { global: { stubs: globalStubs } })

    await wrapper.find('#mod-username').setValue('admin')
    await wrapper.find('#mod-password').setValue('wrong')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.text()).toContain('bad credentials')
    expect(pushMock).not.toHaveBeenCalled()
  })
})
