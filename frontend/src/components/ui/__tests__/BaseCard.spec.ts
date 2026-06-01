import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import BaseCard from '@/components/ui/BaseCard.vue'

describe('BaseCard', () => {
  it('renders slot content', () => {
    const wrapper = mount(BaseCard, { slots: { default: 'hello' } })
    expect(wrapper.text()).toBe('hello')
  })

  it('applies base card classes by default', () => {
    const wrapper = mount(BaseCard)
    expect(wrapper.classes()).toContain('bg-surface')
    expect(wrapper.classes()).toContain('border-border')
  })

  it('adds hover class when interactive', () => {
    const wrapper = mount(BaseCard, { props: { interactive: true } })
    expect(wrapper.classes()).toContain('hover:border-accent')
  })
})

