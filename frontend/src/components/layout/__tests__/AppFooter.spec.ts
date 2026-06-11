import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import AppFooter from '@/components/layout/AppFooter.vue'

describe('AppFooter', () => {
  it('renders the wordmark and the founding year', () => {
    const wrapper = mount(AppFooter)
    expect(wrapper.text()).toContain('ячан')
    expect(wrapper.text()).toContain('est. 2026')
  })

  it('links to the source repository', () => {
    const wrapper = mount(AppFooter)
    const link = wrapper.find('a')
    expect(link.attributes('href')).toBe('https://github.com/Nazar652/yachan-v2')
    expect(link.text()).toContain('source')
  })

  it('credits the author', () => {
    const wrapper = mount(AppFooter)
    expect(wrapper.text()).toContain('made by nazariy von gerste')
  })
})
