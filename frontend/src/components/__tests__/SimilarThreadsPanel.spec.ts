import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import SimilarThreadsPanel from '@/components/SimilarThreadsPanel.vue'
import type { SimilarThreadResponse } from '@/api/types'

const routerLinkStub = { props: ['to'], template: '<a :href="to"><slot /></a>' }
const globalStubs = { RouterLink: routerLinkStub }

function item(overrides: Partial<SimilarThreadResponse> = {}): SimilarThreadResponse {
  return {
    board_slug: 'b',
    thread_id: 2,
    title: 'other thread',
    op_snippet: 'a snippet',
    thumbnail_url: null,
    reply_count: 5,
    score: 0.8,
    ...overrides,
  }
}

describe('SimilarThreadsPanel', () => {
  it('renders a row per item with a link to the thread', () => {
    const wrapper = mount(SimilarThreadsPanel, {
      props: { items: [item()] },
      global: { stubs: globalStubs },
    })

    expect(wrapper.find('details').exists()).toBe(true)
    expect(wrapper.text()).toContain('other thread')
    expect(wrapper.text()).toContain('5 replies')
    expect(wrapper.find('a').attributes('href')).toBe('/b/thread/2')
  })

  it('falls back to the op snippet when the thread has no title', () => {
    const wrapper = mount(SimilarThreadsPanel, {
      props: { items: [item({ title: null })] },
      global: { stubs: globalStubs },
    })

    expect(wrapper.text()).toContain('a snippet')
  })

  it('renders nothing when there are no items', () => {
    const wrapper = mount(SimilarThreadsPanel, {
      props: { items: [] },
      global: { stubs: globalStubs },
    })

    expect(wrapper.find('details').exists()).toBe(false)
  })

  it('does not render a thumbnail image when none is present', () => {
    const wrapper = mount(SimilarThreadsPanel, {
      props: { items: [item({ thumbnail_url: null })] },
      global: { stubs: globalStubs },
    })

    expect(wrapper.find('img').exists()).toBe(false)
  })

  it('renders a thumbnail image when present', () => {
    const wrapper = mount(SimilarThreadsPanel, {
      props: { items: [item({ thumbnail_url: '/media/t.jpg' })] },
      global: { stubs: globalStubs },
    })

    expect(wrapper.find('img').attributes('src')).toBe('/media/t.jpg')
  })
})
