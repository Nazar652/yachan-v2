import { describe, expect, it, vi, beforeEach } from 'vitest'
import { ref } from 'vue'
import { mount, flushPromises, type VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

import ThreadView from '@/views/ThreadView.vue'
import { useThread } from '@/composables/useThread'
import { ApiError } from '@/api/errors'
import { useAuthStore } from '@/stores/auth'

const { routeStub, pushMock } = vi.hoisted(() => ({
  routeStub: { params: { slug: 'b', id: '42' }, hash: '' },
  pushMock: vi.fn(),
}))

vi.mock('vue-router', () => ({
  useRoute: () => routeStub,
  useRouter: () => ({ push: pushMock }),
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
const removeThreadMock = vi.fn()
vi.mock('@/composables/useModeration', () => ({
  useModeration: () => ({
    setLocked: setLockedMock,
    setSticky: setStickyMock,
    removePost: vi.fn(),
    removeThread: removeThreadMock,
    ban: vi.fn(),
  }),
}))

const useThreadMock = vi.mocked(useThread)

function stubThread(state: Record<string, unknown>) {
  useThreadMock.mockReturnValue(state as ReturnType<typeof useThread>)
}

const quoteSpy = vi.fn()

const globalStubs = {
  RouterLink: { template: '<a><slot /></a>' },
  ReplyForm: {
    template: '<form class="reply-form-stub" />',
    setup(_: unknown, { expose }: { expose: (exposed: Record<string, unknown>) => void }) {
      expose({ quote: quoteSpy })
    },
  },
  PostArticle: {
    template: '<article class="post-article-stub" :id="`post-${post.post_number}`" :data-post="post.post_number" :data-backlinks="backlinks.join(\',\')" />',
    props: ['post', 'slug', 'threadId', 'backlinks'],
    emits: ['quote', 'navigate'],
  },
  BaseButton: { template: '<button @click="$emit(\'click\')"><slot /></button>', emits: ['click'] },
  RefPreviews: { template: '<div class="ref-previews-stub" />', props: ['posts', 'slug'], emits: ['navigate'] },
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
  removeThreadMock.mockReset()
  pushMock.mockReset()
  quoteSpy.mockReset()
  routeStub.hash = ''
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

  it('shows the TL;DR panel when the thread has a summary', () => {
    stubThreadDetail({ summary: 'the thread is about cats' })
    const wrapper = mount(ThreadView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('TL;DR')
    expect(wrapper.text()).toContain('the thread is about cats')
  })

  it('omits the TL;DR panel when there is no summary', () => {
    stubThreadDetail({ summary: null })
    const wrapper = mount(ThreadView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).not.toContain('TL;DR')
  })

  it('shows sticky and locked flags', () => {
    stubThreadDetail({ is_locked: true, is_sticky: true, posts: [] })
    const wrapper = mount(ThreadView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('★ sticky')
    expect(wrapper.text()).toContain('⊘ locked')
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

  it('hides the delete-thread button for a moderator', () => {
    useAuthStore().login('jwt', 'moderator')
    stubThreadDetail()
    const wrapper = mount(ThreadView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).not.toContain('Delete thread')
  })

  it('shows the delete-thread button for an admin', () => {
    useAuthStore().login('jwt', 'admin')
    stubThreadDetail()
    const wrapper = mount(ThreadView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('Delete thread')
  })

  it('deletes the thread and navigates to the board on confirm', async () => {
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true)
    removeThreadMock.mockResolvedValue(undefined)
    useAuthStore().login('jwt', 'admin')
    stubThreadDetail()
    const wrapper = mount(ThreadView, { global: { stubs: globalStubs } })

    await clickButton(wrapper, 'Delete thread')
    await flushPromises()

    expect(removeThreadMock).toHaveBeenCalled()
    expect(pushMock).toHaveBeenCalledWith('/b')
    confirmSpy.mockRestore()
  })

  it('does not delete the thread when the confirm is dismissed', async () => {
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false)
    useAuthStore().login('jwt', 'admin')
    stubThreadDetail()
    const wrapper = mount(ThreadView, { global: { stubs: globalStubs } })

    await clickButton(wrapper, 'Delete thread')

    expect(removeThreadMock).not.toHaveBeenCalled()
    expect(pushMock).not.toHaveBeenCalled()
    confirmSpy.mockRestore()
  })

  it('shows the api detail when toggling the lock fails', async () => {
    useAuthStore().login('jwt', 'admin')
    setLockedMock.mockRejectedValue(new ApiError('session expired', 401))
    stubThreadDetail({ is_locked: false })
    const wrapper = mount(ThreadView, { global: { stubs: globalStubs } })
    await clickButton(wrapper, 'Lock')
    await flushPromises()
    expect(wrapper.find('p.text-danger').text()).toBe('session expired')
  })

  it('derives backlinks for a post from the references in other posts', () => {
    stubThreadDetail({
      posts: [
        postFixture,
        { ...postFixture, id: 2, post_number: 102, is_op: false, body_html: '<a class="post-ref" data-post="101">&gt;&gt;101</a>' },
      ],
    })
    const wrapper = mount(ThreadView, { global: { stubs: globalStubs } })
    const opStub = wrapper.find('.post-article-stub[data-post="101"]')
    expect(opStub.attributes('data-backlinks')).toBe('102')
  })

  it('forwards a post quote to the reply form', async () => {
    stubThreadDetail()
    const wrapper = mount(ThreadView, { global: { stubs: globalStubs } })
    await (wrapper.findComponent('.post-article-stub') as VueWrapper).vm.$emit('quote', 101)
    expect(quoteSpy).toHaveBeenCalledWith(101)
  })

  it('scrolls to the referenced post on navigate', async () => {
    const scrollSpy = vi.fn()
    Element.prototype.scrollIntoView = scrollSpy
    stubThreadDetail()
    const wrapper = mount(ThreadView, { global: { stubs: globalStubs }, attachTo: document.body })
    await (wrapper.findComponent('.post-article-stub') as VueWrapper).vm.$emit('navigate', 101)
    expect(scrollSpy).toHaveBeenCalled()
    wrapper.unmount()
  })

  it('scrolls to the post named in the url hash once the thread loads', async () => {
    const scrollSpy = vi.fn()
    Element.prototype.scrollIntoView = scrollSpy
    routeStub.hash = '#post-101'
    stubThreadDetail()
    const wrapper = mount(ThreadView, { global: { stubs: globalStubs }, attachTo: document.body })
    await new Promise((resolve) => setTimeout(resolve))
    expect(scrollSpy).toHaveBeenCalled()
    wrapper.unmount()
  })
})
