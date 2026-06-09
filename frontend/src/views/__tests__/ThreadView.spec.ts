import { describe, expect, it, vi, beforeEach } from 'vitest'
import { ref } from 'vue'
import { mount, flushPromises, type VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

import ThreadView from '@/views/ThreadView.vue'
import { useThread } from '@/composables/useThread'
import { useAuthStore } from '@/stores/auth'

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

const setLockedMock = vi.fn()
const setStickyMock = vi.fn()
const removePostMock = vi.fn()
const banMock = vi.fn()
vi.mock('@/composables/useModeration', () => ({
  useModeration: () => ({
    setLocked: setLockedMock,
    setSticky: setStickyMock,
    removePost: removePostMock,
    ban: banMock,
  }),
}))

const useThreadMock = vi.mocked(useThread)

function stubThread(state: Record<string, unknown>) {
  useThreadMock.mockReturnValue(state as ReturnType<typeof useThread>)
}

const globalStubs = {
  RouterLink: { template: '<a><slot /></a>' },
  ReplyForm: { template: '<form class="reply-form-stub" />' },
  BaseButton: { template: '<button @click="$emit(\'click\')"><slot /></button>', emits: ['click'] },
  BaseInput: {
    template: '<input @input="$emit(\'update:modelValue\', $event.target.value)" />',
    props: ['modelValue'],
    emits: ['update:modelValue'],
  },
}

// click a stubbed button by its visible label (mod controls render many buttons)
function clickButton(wrapper: VueWrapper, label: string) {
  const button = wrapper.findAll('button').find((candidate) => candidate.text() === label)
  if (!button) throw new Error(`button "${label}" not found`)
  return button.trigger('click')
}

beforeEach(() => {
  localStorage.clear()
  setActivePinia(createPinia())
  setLockedMock.mockReset()
  setStickyMock.mockReset()
  removePostMock.mockReset()
  banMock.mockReset()
})

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

  it('renders a gif attachment inline as an image', () => {
    stubThread({
      data: ref({
        id: 42, board_id: 1, title: 'T', is_locked: false, is_sticky: false, reply_count: 1, bump_at: '', created_at: '',
        posts: [
          {
            id: 1, post_number: 1, thread_id: 42, board_id: 1, name: 'Anon', tripcode: null, body: null, body_html: null, sage: false, is_op: true, is_edited: false, edited_at: null, created_at: '2024-01-01T00:00:00',
            attachments: [{ id: 11, media_type: 'gif', original_name: 'anim.gif', url: '/media/anim.gif', thumbnail_url: '/media/anim-thumb.jpg', mime_type: 'image/gif', width: 200, height: 100, size_bytes: 12345, duration_seconds: null }],
          },
        ],
      }),
      isPending: ref(false),
      isError: ref(false),
    })
    const wrapper = mount(ThreadView, { global: { stubs: globalStubs } })
    const img = wrapper.find('img')
    expect(img.exists()).toBe(true)
    expect(img.attributes('src')).toBe('/media/anim.gif')
    expect(wrapper.text()).not.toContain('📎')
  })

  it('renders a video attachment inline with a video element', () => {
    stubThread({
      data: ref({
        id: 42, board_id: 1, title: 'T', is_locked: false, is_sticky: false, reply_count: 1, bump_at: '', created_at: '',
        posts: [
          {
            id: 1, post_number: 1, thread_id: 42, board_id: 1, name: 'Anon', tripcode: null, body: null, body_html: null, sage: false, is_op: true, is_edited: false, edited_at: null, created_at: '2024-01-01T00:00:00',
            attachments: [{ id: 12, media_type: 'video', original_name: 'clip.webm', url: '/media/clip.webm', thumbnail_url: null, mime_type: 'video/webm', width: null, height: null, size_bytes: 99999, duration_seconds: null }],
          },
        ],
      }),
      isPending: ref(false),
      isError: ref(false),
    })
    const wrapper = mount(ThreadView, { global: { stubs: globalStubs } })
    const video = wrapper.find('video')
    expect(video.exists()).toBe(true)
    expect(video.attributes('src')).toBe('/media/clip.webm')
    expect(wrapper.find('img').exists()).toBe(false)
  })

  const postFixture = {
    id: 1, post_number: 101, thread_id: 42, board_id: 1, name: 'Anon', tripcode: null,
    body: 'hi', body_html: '<p>hi</p>', sage: false, is_op: true, is_edited: false,
    edited_at: null, created_at: '2024-01-01T00:00:00', attachments: [],
  }

  function stubAuthedThread(overrides: Record<string, unknown> = {}) {
    stubThread({
      data: ref({
        id: 42, board_id: 1, title: 'T', is_locked: false, is_sticky: false, reply_count: 1,
        bump_at: '', created_at: '', posts: [postFixture], ...overrides,
      }),
      isPending: ref(false),
      isError: ref(false),
    })
  }

  it('hides mod controls when not authenticated', () => {
    stubAuthedThread()
    const wrapper = mount(ThreadView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).not.toContain('Delete')
    expect(wrapper.text()).not.toContain('Lock')
  })

  it('shows mod controls when authenticated', () => {
    useAuthStore().login('jwt', 'admin')
    stubAuthedThread()
    const wrapper = mount(ThreadView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('Lock')
    expect(wrapper.text()).toContain('Sticky')
    expect(wrapper.text()).toContain('Delete')
    expect(wrapper.text()).toContain('Ban')
  })

  it('toggles the thread lock', async () => {
    useAuthStore().login('jwt', 'admin')
    stubAuthedThread({ is_locked: false })
    const wrapper = mount(ThreadView, { global: { stubs: globalStubs } })
    await clickButton(wrapper, 'Lock')
    expect(setLockedMock).toHaveBeenCalledWith(true)
  })

  it('toggles the thread sticky', async () => {
    useAuthStore().login('jwt', 'admin')
    stubAuthedThread({ is_sticky: false })
    const wrapper = mount(ThreadView, { global: { stubs: globalStubs } })
    await clickButton(wrapper, 'Sticky')
    expect(setStickyMock).toHaveBeenCalledWith(true)
  })

  it('deletes a post', async () => {
    useAuthStore().login('jwt', 'admin')
    stubAuthedThread()
    const wrapper = mount(ThreadView, { global: { stubs: globalStubs } })
    await clickButton(wrapper, 'Delete')
    expect(removePostMock).toHaveBeenCalledWith(101)
  })

  it('bans a poster through the inline ban form', async () => {
    useAuthStore().login('jwt', 'admin')
    banMock.mockResolvedValue(undefined)
    stubAuthedThread()
    const wrapper = mount(ThreadView, { global: { stubs: globalStubs } })

    await clickButton(wrapper, 'Ban')
    await wrapper.find('input').setValue('spam')
    await clickButton(wrapper, 'Confirm ban')
    await flushPromises()

    expect(banMock).toHaveBeenCalledWith(101, { reason: 'spam' })
  })
})

