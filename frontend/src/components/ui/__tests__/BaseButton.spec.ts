import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import BaseButton from '@/components/ui/BaseButton.vue'

describe('BaseButton', () => {
  it('renders slot content', () => {
    const wrapper = mount(BaseButton, { slots: { default: 'Post' } })
    expect(wrapper.text()).toBe('Post')
  })

  it('uses the primary variant by default', () => {
    const wrapper = mount(BaseButton)
    expect(wrapper.classes()).toContain('bg-accent')
  })

  it('applies the danger variant', () => {
    const wrapper = mount(BaseButton, { props: { variant: 'danger' } })
    expect(wrapper.classes()).toContain('bg-danger')
  })

  it('can be disabled', () => {
    const wrapper = mount(BaseButton, { props: { disabled: true } })
    expect(wrapper.attributes('disabled')).toBeDefined()
  })
})
