import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import BaseButton from '@/components/ui/BaseButton.vue'

describe('BaseButton', () => {
  it('renders slot content', () => {
    const wrapper = mount(BaseButton, { slots: { default: 'Post' } })
    expect(wrapper.text()).toBe('Post')
  })

  it('uses the gold primary variant by default', () => {
    const wrapper = mount(BaseButton)
    expect(wrapper.classes()).toContain('bg-gold')
  })

  it('applies the danger variant', () => {
    const wrapper = mount(BaseButton, { props: { variant: 'danger' } })
    expect(wrapper.classes()).toContain('bg-danger')
  })

  it('applies the ghost variant with a visible border', () => {
    const wrapper = mount(BaseButton, { props: { variant: 'ghost' } })
    expect(wrapper.classes()).toContain('border-border')
  })

  it('applies the link variant', () => {
    const wrapper = mount(BaseButton, { props: { variant: 'link' } })
    expect(wrapper.classes()).toContain('text-accent')
  })

  it('can be disabled', () => {
    const wrapper = mount(BaseButton, { props: { disabled: true } })
    expect(wrapper.attributes('disabled')).toBeDefined()
  })
})
