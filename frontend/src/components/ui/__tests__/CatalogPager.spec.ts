import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import CatalogPager from '@/components/ui/CatalogPager.vue'

function mountPager(page: number, total: number) {
  return mount(CatalogPager, { props: { page, total } })
}

function pageButtons(wrapper: ReturnType<typeof mountPager>) {
  return wrapper.findAll('button').filter((button) => /^\d+$/.test(button.text()))
}

describe('CatalogPager', () => {
  it('renders nothing for a single page', () => {
    const wrapper = mountPager(1, 1)
    expect(wrapper.find('nav').exists()).toBe(false)
  })

  it('windows the pages around the edges and the current page', () => {
    const wrapper = mountPager(1, 9)
    expect(pageButtons(wrapper).map((button) => button.text())).toEqual(['1', '2', '8', '9'])
    expect(wrapper.text()).toContain('···')
  })

  it('shows the neighbours of the current page', () => {
    const wrapper = mountPager(5, 9)
    expect(pageButtons(wrapper).map((button) => button.text())).toEqual([
      '1', '2', '4', '5', '6', '8', '9',
    ])
  })

  it('marks the current page', () => {
    const wrapper = mountPager(2, 9)
    const current = pageButtons(wrapper).find((button) => button.text() === '2')
    expect(current!.classes()).toContain('bg-gold')
  })

  it('disables prev on the first page and next on the last', () => {
    expect(mountPager(1, 9).find('button').attributes('disabled')).toBeDefined()
    const last = mountPager(9, 9)
    const buttons = last.findAll('button')
    expect(buttons[buttons.length - 1]!.attributes('disabled')).toBeDefined()
  })

  it('emits the selected page', async () => {
    const wrapper = mountPager(1, 9)
    const target = pageButtons(wrapper).find((button) => button.text() === '8')
    await target!.trigger('click')
    expect(wrapper.emitted('update:page')).toEqual([[8]])
  })

  it('does not emit for the already-current page', async () => {
    const wrapper = mountPager(2, 9)
    const current = pageButtons(wrapper).find((button) => button.text() === '2')
    await current!.trigger('click')
    expect(wrapper.emitted('update:page')).toBeUndefined()
  })
})
