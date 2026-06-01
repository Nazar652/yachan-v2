import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import CaptchaWidget from '@/components/ui/CaptchaWidget.vue'

// stub child components to keep test fast and isolated
const globalStubs = {
  BaseButton: { template: '<button @click="$emit(\'click\')"><slot /></button>', emits: ['click'] },
  BaseInput: { template: '<input />' },
}

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

  it('renders the captcha image when data is available', () => {
    const captcha = { token: 'tok', image_base64: 'abc123==' }
    const wrapper = mount(CaptchaWidget, {
      props: { captcha, isPending: false, isError: false, modelValue: '' },
      global: { stubs: globalStubs },
    })
    const img = wrapper.find('img')
    expect(img.exists()).toBe(true)
    expect(img.attributes('src')).toBe('data:image/png;base64,abc123==')
  })

  it('emits refresh when the refresh button is clicked', async () => {
    const captcha = { token: 'tok', image_base64: 'abc==' }
    const wrapper = mount(CaptchaWidget, {
      props: { captcha, isPending: false, isError: false, modelValue: '' },
      global: { stubs: globalStubs },
    })
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('refresh')).toHaveLength(1)
  })
})

