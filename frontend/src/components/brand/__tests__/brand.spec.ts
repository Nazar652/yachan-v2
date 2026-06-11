import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import BarleyEar from '@/components/brand/BarleyEar.vue'
import MonogramSeal from '@/components/brand/MonogramSeal.vue'
import SierpMotif from '@/components/brand/SierpMotif.vue'

describe('BarleyEar', () => {
  it('renders an svg scaled to the height prop', () => {
    const wrapper = mount(BarleyEar, { props: { height: 300 } })
    const svg = wrapper.find('svg')
    expect(svg.attributes('height')).toBe('300')
    expect(svg.attributes('width')).toBe('100')
    expect(svg.attributes('viewBox')).toBe('0 0 100 300')
  })

  it('draws two mirrored paths per grain anchor', () => {
    const wrapper = mount(BarleyEar)
    // 6 anchors * 2 sides + the tip grain
    expect(wrapper.findAll('g')[0]!.findAll('path')).toHaveLength(13)
  })

  it('applies the amber and gold colour props', () => {
    const wrapper = mount(BarleyEar, { props: { amber: 'red', gold: 'blue' } })
    expect(wrapper.find('g').attributes('stroke')).toBe('red')
    expect(wrapper.find('g').attributes('fill')).toBe('blue')
  })
})

describe('MonogramSeal', () => {
  it('renders the hexagon seal with the Я letter', () => {
    const wrapper = mount(MonogramSeal, { props: { size: 92 } })
    expect(wrapper.find('svg').attributes('width')).toBe('92')
    expect(wrapper.find('text').text()).toBe('Я')
  })

  it('uses the fg / bg colour props', () => {
    const wrapper = mount(MonogramSeal, { props: { fg: 'gold', bg: 'black' } })
    expect(wrapper.find('path').attributes('fill')).toBe('black')
    expect(wrapper.find('text').attributes('fill')).toBe('gold')
  })
})

describe('SierpMotif', () => {
  it('renders six triangles', () => {
    const wrapper = mount(SierpMotif)
    expect(wrapper.findAll('polygon')).toHaveLength(6)
  })

  it('scales the viewBox to the size prop', () => {
    const wrapper = mount(SierpMotif, { props: { size: 26 } })
    expect(wrapper.find('svg').attributes('viewBox')).toBe('0 0 26 26')
  })
})
