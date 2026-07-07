import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'

import ThreadGalleryCard from '@/components/ThreadGalleryCard.vue'
import type { ThreadResponse } from '@/api/types'

const { routerLinkStub } = vi.hoisted(() => ({
  routerLinkStub: { props: ['to'], template: '<a :href="to"><slot /></a>' },
}))

vi.mock('vue-router', () => ({
  RouterLink: routerLinkStub,
}))

const globalStubs = { RouterLink: routerLinkStub }

function makeThread(overrides: Partial<ThreadResponse> = {}): ThreadResponse {
  return {
    id: 1,
    board_id: 1,
    title: 'First thread',
    is_locked: false,
    is_sticky: false,
    reply_count: 10,
    bump_at: '2026-06-10T12:53:00Z',
    created_at: '2026-06-08T20:34:00Z',
    op_post: {
      body: 'Yeah, i did it.',
      body_html: '<p>Yeah, i did it.</p>',
      thumbnail_url: '/media/t.jpg',
    },
    last_replies: [],
    ...overrides,
  } as ThreadResponse
}

function mountCard(thread: ThreadResponse) {
  return mount(ThreadGalleryCard, {
    props: { thread, slug: 'b' },
    global: { stubs: globalStubs },
  })
}

describe('ThreadGalleryCard', () => {
  it('links to the thread', () => {
    const wrapper = mountCard(makeThread())
    expect(wrapper.attributes('href')).toBe('/b/thread/1')
  })

  it('renders the thumbnail when the op has one', () => {
    const wrapper = mountCard(makeThread())
    expect(wrapper.find('img').attributes('src')).toBe('/media/t.jpg')
  })

  it('shows a placeholder when there is no thumbnail', () => {
    const wrapper = mountCard(makeThread({ op_post: { body: 'x', body_html: '<p>x</p>', thumbnail_url: null } }))
    expect(wrapper.find('img').exists()).toBe(false)
    expect(wrapper.text()).toContain('no image')
  })

  it('shows the title and reply count', () => {
    const wrapper = mountCard(makeThread({ reply_count: 7 }))
    expect(wrapper.text()).toContain('First thread')
    expect(wrapper.text()).toContain('R: 7')
  })

  it('shows the image count alongside the reply count', () => {
    const image = { url: '/media/f.jpg', thumbnail_url: '/media/t.jpg', width: 1, height: 1 }
    const wrapper = mountCard(
      makeThread({
        op_post: {
          body: 'x',
          body_html: '<p>x</p>',
          thumbnail_url: '/media/t.jpg',
          images: [image, image],
        },
      } as Partial<ThreadResponse>),
    )
    expect(wrapper.text()).toContain('R: 10 / I: 2')
  })

  it('defaults the image count to 0 when the op has no images field', () => {
    const wrapper = mountCard(makeThread())
    expect(wrapper.text()).toContain('R: 10 / I: 0')
  })

  it('renders the formatted op text via PostBody', () => {
    const wrapper = mountCard(
      makeThread({
        op_post: {
          body: 'plain',
          body_html: '<p>plain <span class="greentext">&gt;implying</span></p>',
          thumbnail_url: '/media/t.jpg',
        },
      } as Partial<ThreadResponse>),
    )
    expect(wrapper.find('.post-body').exists()).toBe(true)
    expect(wrapper.find('.greentext').exists()).toBe(true)
  })

  it('shows a placeholder when the op has no text', () => {
    const wrapper = mountCard(
      makeThread({
        op_post: { body: null, body_html: null, thumbnail_url: null },
      } as Partial<ThreadResponse>),
    )
    expect(wrapper.text()).toContain('No text.')
  })

  it('falls back to a truncated op body when the thread has no title', () => {
    const wrapper = mountCard(makeThread({ title: null, op_post: { body: 'x'.repeat(80), body_html: '<p></p>', thumbnail_url: null } }))
    expect(wrapper.text()).toContain(`${'x'.repeat(60)}…`)
  })

  it('falls back to a placeholder title when there is no title or op body', () => {
    const wrapper = mountCard(makeThread({ title: null, op_post: { body: null, body_html: null, thumbnail_url: null } }))
    expect(wrapper.text()).toContain('(no title)')
  })

  it('shows a sticky badge', () => {
    const wrapper = mountCard(makeThread({ is_sticky: true }))
    expect(wrapper.text()).toContain('📌')
  })

  it('shows a locked badge', () => {
    const wrapper = mountCard(makeThread({ is_locked: true }))
    expect(wrapper.text()).toContain('🔒')
  })

  it('hides badges for a thread that is neither locked nor sticky', () => {
    const wrapper = mountCard(makeThread())
    expect(wrapper.text()).not.toContain('📌')
    expect(wrapper.text()).not.toContain('🔒')
  })
})
