import { describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'
import { mount } from '@vue/test-utils'

import ThreadView from '@/views/ThreadView.vue'
import { useThread } from '@/composables/useThread'

vi.mock('vue-router', () => ({
  useRoute: () => ({ params: { slug: 'b', id: '42' } }),
  RouterLink: { template: '<a><slot /></a>' },
}))

vi.mock('@/composables/useThread', () => ({
  useThread: vi.fn(),
}))

vi.mock('@/composables/useThreadWs', () => ({
  useThreadWs: vi.fn(),
}))

const useThreadMock = vi.mocked(useThread)

function stubThread(state: Record<string, unknown>) {
  useThreadMock.mockReturnValue(state as ReturnType<typeof useThread>)
}

const globalStubs = {
  RouterLink: { template: '<a><slot /></a>' },
  ReplyForm: { template: '<form class="reply-form-stub" />' },
}

describe('ThreadView', () => {
  it('shows loading state while pending', () => {
    stubThread({ data: ref(undefined), isPending: ref(true), isError: ref(false) })
    const wrapper = mount(ThreadView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('Loading')
  })

  it('shows error state on failure', () => {
    stubThread({ data: ref(undefined), isPending: ref(false), isError: ref(true) })
    const wrapper = mount(ThreadView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('Failed to load thread')
  })

  it('renders thread title', () => {
    stubThread({
      data: ref({ id: 42, board_id: 1, title: 'My Thread', is_locked: false, is_sticky: false, reply_count: 2, bump_at: '', created_at: '', posts: [] }),
      isPending: ref(false),
      isError: ref(false),
    })
    const wrapper = mount(ThreadView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('My Thread')
  })

  it('shows (no title) when thread title is null', () => {
    stubThread({
      data: ref({ id: 42, board_id: 1, title: null, is_locked: false, is_sticky: false, reply_count: 0, bump_at: '', created_at: '', posts: [] }),
      isPending: ref(false),
      isError: ref(false),
    })
    const wrapper = mount(ThreadView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('(no title)')
  })

  it('renders post name and post number', () => {
    stubThread({
      data: ref({
        id: 42, board_id: 1, title: 'T', is_locked: false, is_sticky: false, reply_count: 1, bump_at: '', created_at: '',
        posts: [
          { id: 1, post_number: 101, thread_id: 42, board_id: 1, name: 'Anon', tripcode: null, body: 'Hello', body_html: '<p>Hello</p>', sage: false, is_op: true, is_edited: false, edited_at: null, created_at: '2024-01-01T00:00:00', attachments: [] },
        ],
      }),
      isPending: ref(false),
      isError: ref(false),
    })
    const wrapper = mount(ThreadView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('Anon')
    expect(wrapper.text()).toContain('No.101')
  })

  it('shows sticky and locked icons', () => {
    stubThread({
      data: ref({ id: 42, board_id: 1, title: 'T', is_locked: true, is_sticky: true, reply_count: 0, bump_at: '', created_at: '', posts: [] }),
      isPending: ref(false),
      isError: ref(false),
    })
    const wrapper = mount(ThreadView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('📌')
    expect(wrapper.text()).toContain('🔒')
  })

  it('renders tripcode when present', () => {
    stubThread({
      data: ref({
        id: 42, board_id: 1, title: 'T', is_locked: false, is_sticky: false, reply_count: 1, bump_at: '', created_at: '',
        posts: [
          { id: 1, post_number: 1, thread_id: 42, board_id: 1, name: 'User', tripcode: '!xKvLoKvAbC', body: null, body_html: null, sage: false, is_op: false, is_edited: false, edited_at: null, created_at: '2024-01-01T00:00:00', attachments: [] },
        ],
      }),
      isPending: ref(false),
      isError: ref(false),
    })
    const wrapper = mount(ThreadView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('!xKvLoKvAbC')
  })

  it('shows (edited) label on edited posts', () => {
    stubThread({
      data: ref({
        id: 42, board_id: 1, title: 'T', is_locked: false, is_sticky: false, reply_count: 1, bump_at: '', created_at: '',
        posts: [
          { id: 1, post_number: 1, thread_id: 42, board_id: 1, name: 'Anon', tripcode: null, body: 'edited', body_html: '<p>edited</p>', sage: false, is_op: false, is_edited: true, edited_at: '2024-01-02T00:00:00', created_at: '2024-01-01T00:00:00', attachments: [] },
        ],
      }),
      isPending: ref(false),
      isError: ref(false),
    })
    const wrapper = mount(ThreadView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('edited')
  })

  it('shows the reply form when the thread is not locked', () => {
    stubThread({
      data: ref({ id: 42, board_id: 1, title: 'T', is_locked: false, is_sticky: false, reply_count: 0, bump_at: '', created_at: '', posts: [] }),
      isPending: ref(false),
      isError: ref(false),
    })
    const wrapper = mount(ThreadView, { global: { stubs: globalStubs } })
    expect(wrapper.find('.reply-form-stub').exists()).toBe(true)
  })

  it('hides the reply form and shows a locked message when the thread is locked', () => {
    stubThread({
      data: ref({ id: 42, board_id: 1, title: 'T', is_locked: true, is_sticky: false, reply_count: 0, bump_at: '', created_at: '', posts: [] }),
      isPending: ref(false),
      isError: ref(false),
    })
    const wrapper = mount(ThreadView, { global: { stubs: globalStubs } })
    expect(wrapper.find('.reply-form-stub').exists()).toBe(false)
    expect(wrapper.text()).toContain('locked')
  })

  it('renders an image attachment', () => {
    stubThread({
      data: ref({
        id: 42, board_id: 1, title: 'T', is_locked: false, is_sticky: false, reply_count: 1, bump_at: '', created_at: '',
        posts: [
          {
            id: 1, post_number: 1, thread_id: 42, board_id: 1, name: 'Anon', tripcode: null, body: null, body_html: null, sage: false, is_op: true, is_edited: false, edited_at: null, created_at: '2024-01-01T00:00:00',
            attachments: [{ id: 10, media_type: 'image', original_name: 'photo.jpg', url: '/media/photo.jpg', thumbnail_url: '/media/thumb.jpg', mime_type: 'image/jpeg', width: 800, height: 600, size_bytes: 51200, duration_seconds: null }],
          },
        ],
      }),
      isPending: ref(false),
      isError: ref(false),
    })
    const wrapper = mount(ThreadView, { global: { stubs: globalStubs } })
    const img = wrapper.find('img')
    expect(img.exists()).toBe(true)
    expect(img.attributes('src')).toBe('/media/thumb.jpg')
  })
})

