import { describe, expect, it, vi, beforeEach } from 'vitest'
import { ref } from 'vue'
import { mount, type VueWrapper } from '@vue/test-utils'
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
vi.mock('@/composables/useModeration', () => ({
  useModeration: () => ({
    setLocked: setLockedMock,
    setSticky: setStickyMock,
    removePost: vi.fn(),
    ban: vi.fn(),
  }),
}))

const useThreadMock = vi.mocked(useThread)

function stubThread(state: Record<string, unknown>) {
  useThreadMock.mockReturnValue(state as ReturnType<typeof useThread>)
}

const globalStubs = {
  RouterLink: { template: '<a><slot /></a>' },
  ReplyForm: { template: '<form class="reply-form-stub" />' },
  PostArticle: {
    template: '<article class="post-article-stub" :data-post="post.post_number" />',
    props: ['post', 'slug', 'threadId'],
  },
  BaseButton: { template: '<button @click="$emit(\'click\')"><slot /></button>', emits: ['click'] },
}

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
})

const postFixture = {
  id: 1, post_number: 101, thread_id: 42, board_id: 1, name: 'Anon', tripcode: null,
  body: 'hi', body_html: '<p>hi</p>', sage: false, is_op: true, is_edited: false,
  edited_at: null, created_at: '2024-01-01T00:00:00', can_edit: false, attachments: [],
}

function stubThreadDetail(overrides: Record<string, unknown> = {}) {
  stubThread({
    data: ref({
      id: 42, board_id: 1, title: 'T', is_locked: false, is_sticky: false, reply_count: 1,
      bump_at: '', created_at: '', posts: [postFixture], ...overrides,
    }),
    isPending: ref(false),
    isError: ref(false),
  })
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
    stubThreadDetail({ title: 'My Thread' })
    const wrapper = mount(ThreadView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('My Thread')
  })

  it('shows (no title) when thread title is null', () => {
    stubThreadDetail({ title: null })
    const wrapper = mount(ThreadView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('(no title)')
  })

  it('renders a PostArticle per post', () => {
    stubThreadDetail({ posts: [postFixture, { ...postFixture, id: 2, post_number: 102 }] })
    const wrapper = mount(ThreadView, { global: { stubs: globalStubs } })
    expect(wrapper.findAll('.post-article-stub')).toHaveLength(2)
  })

  it('shows sticky and locked icons', () => {
    stubThreadDetail({ is_locked: true, is_sticky: true, posts: [] })
    const wrapper = mount(ThreadView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('📌')
    expect(wrapper.text()).toContain('🔒')
  })

  it('shows the reply form when the thread is not locked', () => {
    stubThreadDetail({ posts: [] })
    const wrapper = mount(ThreadView, { global: { stubs: globalStubs } })
    expect(wrapper.find('.reply-form-stub').exists()).toBe(true)
  })

  it('hides the reply form and shows a locked message when the thread is locked', () => {
    stubThreadDetail({ is_locked: true, posts: [] })
    const wrapper = mount(ThreadView, { global: { stubs: globalStubs } })
    expect(wrapper.find('.reply-form-stub').exists()).toBe(false)
    expect(wrapper.text()).toContain('locked')
  })

  it('hides thread mod controls when not authenticated', () => {
    stubThreadDetail()
    const wrapper = mount(ThreadView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).not.toContain('Lock')
  })

  it('shows thread mod controls when authenticated', () => {
    useAuthStore().login('jwt', 'admin')
    stubThreadDetail()
    const wrapper = mount(ThreadView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('Lock')
    expect(wrapper.text()).toContain('Sticky')
  })

  it('toggles the thread lock', async () => {
    useAuthStore().login('jwt', 'admin')
    stubThreadDetail({ is_locked: false })
    const wrapper = mount(ThreadView, { global: { stubs: globalStubs } })
    await clickButton(wrapper, 'Lock')
    expect(setLockedMock).toHaveBeenCalledWith(true)
  })

  it('toggles the thread sticky', async () => {
    useAuthStore().login('jwt', 'admin')
    stubThreadDetail({ is_sticky: false })
    const wrapper = mount(ThreadView, { global: { stubs: globalStubs } })
    await clickButton(wrapper, 'Sticky')
    expect(setStickyMock).toHaveBeenCalledWith(true)
  })
})
