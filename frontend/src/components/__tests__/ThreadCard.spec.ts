import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'

import ThreadCard from '@/components/ThreadCard.vue'
import type { ThreadResponse } from '@/api/types'

const { pushMock, routerLinkStub } = vi.hoisted(() => ({
  pushMock: vi.fn(),
  routerLinkStub: { props: ['to'], template: '<a :href="to"><slot /></a>' },
}))

vi.mock('vue-router', () => ({
  RouterLink: routerLinkStub,
  useRouter: () => ({ push: pushMock }),
}))

const globalStubs = { RouterLink: routerLinkStub }

beforeEach(() => {
  pushMock.mockClear()
})

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
      images: [{ url: '/media/f.jpg', thumbnail_url: '/media/t.jpg', width: 400, height: 300 }],
    },
    last_replies: [],
    ...overrides,
  } as ThreadResponse
}

function mountCard(thread: ThreadResponse, isMod = false) {
  return mount(ThreadCard, {
    props: { thread, slug: 'b', isMod },
    global: { stubs: globalStubs },
  })
}

describe('ThreadCard', () => {
  it('renders the head with number, title and counters', () => {
    const wrapper = mountCard(makeThread())
    expect(wrapper.text()).toContain('No.1')
    expect(wrapper.text()).toContain('First thread')
    expect(wrapper.text()).toContain('10 replies')
    expect(wrapper.text()).toContain('1 img')
  })

  it('shows (no title) for an untitled thread', () => {
    const wrapper = mountCard(makeThread({ title: null }))
    expect(wrapper.text()).toContain('(no title)')
  })

  it('shows sticky and locked flags', () => {
    const wrapper = mountCard(makeThread({ is_sticky: true, is_locked: true }))
    expect(wrapper.text()).toContain('★ sticky')
    expect(wrapper.text()).toContain('⊘ locked')
  })

  it('renders a single image inside the left column without a gallery', () => {
    const wrapper = mountCard(makeThread())
    expect(wrapper.findAll('img')).toHaveLength(1)
    expect(wrapper.find('.overflow-x-auto').exists()).toBe(false)
  })

  it('sizes a landscape single image by width keeping its aspect ratio', () => {
    // 400x300 -> ratio 4:3 -> 340 wide, 255 tall
    const style = mountCard(makeThread()).find('img').attributes('style')
    expect(style).toContain('width: 340px')
    expect(style).toContain('height: 255px')
  })

  it('caps a square single image by height keeping its aspect ratio', () => {
    const wrapper = mountCard(
      makeThread({
        op_post: {
          body: 'x',
          body_html: '<p>x</p>',
          thumbnail_url: '/media/t.jpg',
          images: [{ url: '/media/f.jpg', thumbnail_url: '/media/t.jpg', width: 1000, height: 1000 }],
        },
      } as Partial<ThreadResponse>),
    )
    const style = wrapper.find('img').attributes('style')
    expect(style).toContain('width: 260px')
    expect(style).toContain('height: 260px')
  })

  it('clamps extreme aspect ratios at 1:4', () => {
    const wrapper = mountCard(
      makeThread({
        op_post: {
          body: 'x',
          body_html: '<p>x</p>',
          thumbnail_url: '/media/t.jpg',
          images: [{ url: '/media/f.jpg', thumbnail_url: '/media/t.jpg', width: 100, height: 1000 }],
        },
      } as Partial<ThreadResponse>),
    )
    const style = wrapper.find('img').attributes('style')
    expect(style).toContain('width: 65px')
    expect(style).toContain('height: 260px')
  })

  it('falls back to a square thumbnail when dimensions are missing', () => {
    const wrapper = mountCard(
      makeThread({
        op_post: {
          body: 'x',
          body_html: '<p>x</p>',
          thumbnail_url: '/media/t.jpg',
          images: [{ url: '/media/f.jpg', thumbnail_url: '/media/t.jpg', width: null, height: null }],
        },
      } as Partial<ThreadResponse>),
    )
    const style = wrapper.find('img').attributes('style')
    expect(style).toContain('width: 200px')
    expect(style).toContain('height: 200px')
  })

  it('renders a gallery row when the op has several images', () => {
    const image = { url: '/media/f.jpg', thumbnail_url: '/media/t.jpg', width: 1, height: 1 }
    const wrapper = mountCard(
      makeThread({
        op_post: {
          body: 'x',
          body_html: '<p>x</p>',
          thumbnail_url: '/media/t.jpg',
          images: [image, image, image],
        },
      } as Partial<ThreadResponse>),
    )
    expect(wrapper.find('.overflow-x-auto').exists()).toBe(true)
    expect(wrapper.findAll('img')).toHaveLength(3)
    expect(wrapper.text()).toContain('3 img')
  })

  it('sizes gallery tiles by a fixed height and the image ratio', () => {
    const wide = { url: '/media/f.jpg', thumbnail_url: '/media/t.jpg', width: 200, height: 100 }
    const unknown = { url: '/media/f.jpg', thumbnail_url: '/media/t.jpg', width: null, height: null }
    const wrapper = mountCard(
      makeThread({
        op_post: {
          body: 'x',
          body_html: '<p>x</p>',
          thumbnail_url: '/media/t.jpg',
          images: [wide, unknown],
        },
      } as Partial<ThreadResponse>),
    )
    const styles = wrapper.findAll('img').map((img) => img.attributes('style'))
    expect(styles[0]).toContain('width: 228px')
    expect(styles[0]).toContain('height: 114px')
    expect(styles[1]).toContain('width: 148px')
    expect(styles[1]).toContain('height: 114px')
  })

  it('renders the op text and clamps long bodies behind a read-more link', () => {
    const longBody = 'x'.repeat(400)
    const wrapper = mountCard(
      makeThread({
        op_post: {
          body: longBody,
          body_html: `<p>${longBody}</p>`,
          thumbnail_url: null,
          images: [],
        },
      } as Partial<ThreadResponse>),
    )
    expect(wrapper.find('.post-body').exists()).toBe(true)
    expect(wrapper.text()).toContain('Read more →')
  })

  it('shows a placeholder when the op has no text', () => {
    const wrapper = mountCard(
      makeThread({
        op_post: { body: null, body_html: null, thumbnail_url: null, images: [] },
      } as Partial<ThreadResponse>),
    )
    expect(wrapper.text()).toContain('No text.')
  })

  it('lists the latest replies with their post numbers linking to that post', () => {
    const wrapper = mountCard(
      makeThread({
        last_replies: [
          { id: 11, post_number: 37, name: 'Anonymous', body: 'can you see this', body_html: '<p>can you see this</p>', created_at: '2026-06-09T00:44:19Z' },
          { id: 12, post_number: 38, name: 'Anonymous', body: 'yes', body_html: '<p>yes</p>', created_at: '2026-06-09T00:45:57Z' },
        ],
      }),
    )
    expect(wrapper.text()).toContain('Latest 2 replies')
    expect(wrapper.text()).toContain('No.37')
    expect(wrapper.text()).toContain('can you see this')
    const replyLink = wrapper.findAll('a').find((a) => a.text().includes('No.37'))
    expect(replyLink?.attributes('href')).toBe('/b/thread/1#post-37')
  })

  it('opens the thread when the card is clicked', async () => {
    const wrapper = mountCard(makeThread())
    await wrapper.find('article').trigger('click')
    expect(pushMock).toHaveBeenCalledWith('/b/thread/1')
  })

  it('does not open the thread when a reply is clicked', async () => {
    const wrapper = mountCard(
      makeThread({
        last_replies: [
          { id: 11, post_number: 37, name: 'Anonymous', body: 'x', body_html: '<p>x</p>', created_at: '2026-06-09T00:44:19Z' },
        ],
      }),
    )
    const replyLink = wrapper.findAll('a').find((a) => a.text().includes('No.37'))
    await replyLink!.trigger('click')
    expect(pushMock).not.toHaveBeenCalled()
  })

  it('does not open the thread when a mod button is clicked', async () => {
    const wrapper = mountCard(makeThread(), true)
    await wrapper.findAll('button')[0]!.trigger('click')
    expect(pushMock).not.toHaveBeenCalled()
  })

  it('invites the first reply when the thread is empty', () => {
    const wrapper = mountCard(makeThread())
    expect(wrapper.text()).toContain('be the first to sow')
  })

  it('hides the mod bar for anonymous visitors', () => {
    const wrapper = mountCard(makeThread())
    expect(wrapper.findAll('button')).toHaveLength(0)
  })

  it('emits mod toggles from the mod bar', async () => {
    const wrapper = mountCard(makeThread(), true)
    const buttons = wrapper.findAll('button')
    await buttons[0]!.trigger('click')
    await buttons[1]!.trigger('click')
    expect(wrapper.emitted('toggle-lock')).toHaveLength(1)
    expect(wrapper.emitted('toggle-sticky')).toHaveLength(1)
  })
})
