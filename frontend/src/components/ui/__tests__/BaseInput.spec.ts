import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import BaseInput from '@/components/ui/BaseInput.vue'

describe('BaseInput', () => {
  it('binds v-model to the input value', async () => {
    const wrapper = mount(BaseInput, { props: { modelValue: 'a' } })
    await wrapper.find('input').setValue('barley')
    const updates = wrapper.emitted('update:modelValue')!
    expect(updates[updates.length - 1]).toEqual(['barley'])
  })

  it('passes type and placeholder through', () => {
    const wrapper = mount(BaseInput, { props: { type: 'password', placeholder: 'secret' } })
    const input = wrapper.find('input')
    expect(input.attributes('type')).toBe('password')
    expect(input.attributes('placeholder')).toBe('secret')
  })
})
