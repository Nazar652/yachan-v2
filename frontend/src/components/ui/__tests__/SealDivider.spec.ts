import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import SealDivider from '@/components/ui/SealDivider.vue'
import SierpMotif from '@/components/brand/SierpMotif.vue'

describe('SealDivider', () => {
  it('renders the motif between two rule lines', () => {
    const wrapper = mount(SealDivider)
    expect(wrapper.findComponent(SierpMotif).exists()).toBe(true)
    expect(wrapper.findAll('span')).toHaveLength(2)
  })
})
