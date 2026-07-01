import { afterEach, describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import CaptchaWidget from '@/components/ui/CaptchaWidget.vue'
import { useTheme } from '@/composables/useTheme'

// stub child components to keep test fast and isolated
const globalStubs = {
  BaseButton: { template: '<button @click="$emit(\'click\')"><slot /></button>', emits: ['click'] },
  BaseInput: { template: '<input />' },
}

// useTheme() is a module-level singleton shared with the widget under test,
// so directly poking `theme.value` simulates a toggle from elsewhere (e.g. AppHeader)
const themeState = useTheme()

afterEach(() => {
  themeState.theme.value = 'light'
})

describe('CaptchaWidget', () => {
  it('shows loading text while pending', () => {
    const wrapper = mount(CaptchaWidget, {
      props: { captcha: undefined, isPending: true, isError: false, modelValue: '' },
      global: { stubs: globalStubs },
    })
    expect(wrapper.text()).toContain('Loading')
  })

  it('shows error text when captcha fetch fails', () => {
    const wrapper = mount(CaptchaWidget, {
      props: { captcha: undefined, isPending: false, isError: true, modelValue: '' },
      global: { stubs: globalStubs },
    })
    expect(wrapper.text()).toContain('Failed')
  })

  it('renders the light image when the theme is light', () => {
    const captcha = { token: 'tok', image_base64_light: 'light123==', image_base64_dark: 'dark123==' }
    const wrapper = mount(CaptchaWidget, {
      props: { captcha, isPending: false, isError: false, modelValue: '' },
      global: { stubs: globalStubs },
    })
    const img = wrapper.find('img')
    expect(img.exists()).toBe(true)
    expect(img.attributes('src')).toBe('data:image/png;base64,light123==')
  })

  it('renders the dark image when the theme is dark', () => {
    themeState.theme.value = 'dark'
    const captcha = { token: 'tok', image_base64_light: 'light123==', image_base64_dark: 'dark123==' }
    const wrapper = mount(CaptchaWidget, {
      props: { captcha, isPending: false, isError: false, modelValue: '' },
      global: { stubs: globalStubs },
    })
    expect(wrapper.find('img').attributes('src')).toBe('data:image/png;base64,dark123==')
  })

  it('swaps the displayed image reactively when the theme changes', async () => {
    const captcha = { token: 'tok', image_base64_light: 'light123==', image_base64_dark: 'dark123==' }
    const wrapper = mount(CaptchaWidget, {
      props: { captcha, isPending: false, isError: false, modelValue: '' },
      global: { stubs: globalStubs },
    })

    themeState.theme.value = 'dark'
    await wrapper.vm.$nextTick()

    expect(wrapper.find('img').attributes('src')).toBe('data:image/png;base64,dark123==')
  })

  it('emits refresh when the refresh button is clicked', async () => {
    const captcha = { token: 'tok', image_base64_light: 'abc==', image_base64_dark: 'def==' }
    const wrapper = mount(CaptchaWidget, {
      props: { captcha, isPending: false, isError: false, modelValue: '' },
      global: { stubs: globalStubs },
    })
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('refresh')).toHaveLength(1)
  })
})

