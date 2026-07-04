import { describe, expect, it, vi, beforeEach } from 'vitest'
import { ref } from 'vue'
import { mount, flushPromises, type VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

import PostArticle from '@/components/PostArticle.vue'
import { ApiError } from '@/api/errors'
import { useAuthStore } from '@/stores/auth'

const { editPostMock, removePostMock, banMock, usePostHistoryMock, isOwnMock, createReportMock } =
  vi.hoisted(() => ({
    editPostMock: vi.fn(),
    removePostMock: vi.fn(),
    banMock: vi.fn(),
    usePostHistoryMock: vi.fn(),
    isOwnMock: vi.fn(),
    createReportMock: vi.fn(),
  }))

vi.mock('@/composables/useEditPost', () => ({
  useEditPost: () => ({ editPost: editPostMock }),
}))

vi.mock('@/composables/useOwnPosts', () => ({
  useOwnPosts: () => ({ isOwn: isOwnMock }),
}))

vi.mock('@/composables/useModeration', () => ({
  useModeration: () => ({ removePost: removePostMock, ban: banMock, setLocked: vi.fn(), setSticky: vi.fn() }),
}))

vi.mock('@/composables/usePostHistory', () => ({
  usePostHistory: usePostHistoryMock,
}))

vi.mock('@/api/reports', () => ({
  createReport: createReportMock,
}))

const stubs = {
  BaseButton: {
    template: '<button @click="$emit(\'click\')" @mouseenter="$emit(\'mouseenter\')" @mouseleave="$emit(\'mouseleave\')"><slot /></button>',
    emits: ['click', 'mouseenter', 'mouseleave'],
  },
  BaseInput: {
    template: '<input @input="$emit(\'update:modelValue\', $event.target.value)" />',
    props: ['modelValue'],
    emits: ['update:modelValue'],
  },
}

const basePost = {
  id: 1, post_number: 101, thread_id: 42, board_id: 1, name: 'Anon', tripcode: null,
  body: 'hi', body_html: '<p>hi</p>', sage: false, is_op: true, is_edited: false,
  edited_at: null, created_at: '2024-01-01T00:00:00', can_edit: false, attachments: [],
}

function mountPost(overrides: Record<string, unknown> = {}) {
  return mount(PostArticle, {
    props: { post: { ...basePost, ...overrides }, slug: 'b', threadId: 42 },
    global: { stubs },
  })
}

function clickButton(wrapper: VueWrapper, label: string) {
  const button = wrapper.findAll('button').find((candidate) => candidate.text() === label)
  if (!button) throw new Error(`button "${label}" not found`)
  return button
}

beforeEach(() => {
  localStorage.clear()
  setActivePinia(createPinia())
  editPostMock.mockReset().mockResolvedValue(undefined)
  removePostMock.mockReset().mockResolvedValue(undefined)
  banMock.mockReset().mockResolvedValue(undefined)
  usePostHistoryMock.mockReset().mockReturnValue({ data: ref(undefined) })
  isOwnMock.mockReset().mockReturnValue(false)
  createReportMock.mockReset().mockResolvedValue(undefined)
})

describe('PostArticle', () => {
  it('renders the post header and body', () => {
    const wrapper = mountPost({ tripcode: '!abc', sage: true })
    expect(wrapper.text()).toContain('Anon')
    expect(wrapper.text()).toContain('No.101')
    expect(wrapper.text()).toContain('!abc')
    expect(wrapper.text()).toContain('sage')
    expect(wrapper.find('.post-body').html()).toContain('<p>hi</p>')
  })

  it('tags the header with (You) for your own post', () => {
    isOwnMock.mockImplementation((postNumber: number) => postNumber === 101)
    const wrapper = mountPost()
    expect(wrapper.find('.post-you').text()).toBe('(You)')
  })

  it('omits the (You) tag on posts that are not yours', () => {
    const wrapper = mountPost()
    expect(wrapper.find('.post-you').exists()).toBe(false)
  })

  it('emits quote with the post number when the No. button is clicked', async () => {
    const wrapper = mountPost()
    await wrapper.find('button[title="Quote this post"]').trigger('click')
    expect(wrapper.emitted('quote')).toEqual([[101]])
  })

  it('forwards navigate from a >>N reference clicked in the body', async () => {
    const wrapper = mountPost({ body_html: '<a class="post-ref" data-post="55">&gt;&gt;55</a>' })
    await wrapper.find('.post-body a.post-ref').trigger('click')
    expect(wrapper.emitted('navigate')).toEqual([[55]])
  })

  it('renders the backlinks footer and emits navigate when a backlink is clicked', async () => {
    const wrapper = mount(PostArticle, {
      props: { post: basePost, slug: 'b', threadId: 42, backlinks: [102, 103] },
      global: { stubs },
    })
    const refs = wrapper.findAll('.post-backlinks a.post-ref')
    expect(refs.map((ref) => ref.text())).toEqual(['>>102', '>>103'])
    await refs[0]!.trigger('click')
    expect(wrapper.emitted('navigate')).toEqual([[102]])
  })

  it('tags a backlink from your own post with (You)', () => {
    isOwnMock.mockImplementation((postNumber: number) => postNumber === 102)
    const wrapper = mount(PostArticle, {
      props: { post: basePost, slug: 'b', threadId: 42, backlinks: [102, 103] },
      global: { stubs },
    })
    const tagged = wrapper.findAll('.post-backlinks .post-you')
    expect(tagged).toHaveLength(1)
    expect(tagged[0]!.text()).toBe('(You)')
  })

  it('omits the backlinks footer when there are no backlinks', () => {
    const wrapper = mountPost()
    expect(wrapper.find('.post-backlinks').exists()).toBe(false)
  })

  it('shows the edited chip on edited posts', () => {
    const wrapper = mountPost({ is_edited: true })
    expect(wrapper.text()).toContain('edited')
  })

  it('numbers the lines of code blocks in the body', () => {
    const wrapper = mountPost({ body_html: '<pre><code>a\nb\n</code></pre>' })
    const lines = wrapper.findAll('.code-line')
    expect(lines.map((line) => line.text())).toEqual(['a', 'b'])
  })

  it('renders an image attachment with its thumbnail', () => {
    const wrapper = mountPost({
      attachments: [{ id: 10, media_type: 'image', original_name: 'p.jpg', url: '/media/p.jpg', thumbnail_url: '/media/t.jpg', mime_type: 'image/jpeg', width: 1, height: 1, size_bytes: 10, duration_seconds: null }],
    })
    expect(wrapper.find('img').attributes('src')).toBe('/media/t.jpg')
  })

  it('renders a video attachment with a video element', () => {
    const wrapper = mountPost({
      attachments: [{ id: 12, media_type: 'video', original_name: 'c.webm', url: '/media/c.webm', thumbnail_url: null, mime_type: 'video/webm', width: null, height: null, size_bytes: 10, duration_seconds: null }],
    })
    expect(wrapper.find('video').attributes('src')).toBe('/media/c.webm')
  })

  it('renders a placeholder instead of a blocked attachment', () => {
    const wrapper = mountPost({
      attachments: [{ id: 20, media_type: 'image', original_name: 'x.jpg', url: null, thumbnail_url: null, mime_type: 'image/jpeg', width: null, height: null, size_bytes: 10, duration_seconds: null, moderation_status: 'blocked' }],
    })
    expect(wrapper.find('img').exists()).toBe(false)
    expect(wrapper.text()).toContain('removed by moderation')
  })

  it('labels a flagged hidden attachment as 18+', () => {
    const wrapper = mountPost({
      attachments: [{ id: 21, media_type: 'image', original_name: 'x.jpg', url: null, thumbnail_url: null, mime_type: 'image/jpeg', width: null, height: null, size_bytes: 10, duration_seconds: null, moderation_status: 'flagged' }],
    })
    expect(wrapper.text()).toContain('18+')
  })

  it('hides the Edit button when the post is not editable', () => {
    const wrapper = mountPost({ can_edit: false })
    expect(wrapper.findAll('button').some((button) => button.text() === 'Edit')).toBe(false)
  })

  it('shows the Edit button only to the author of an editable post', () => {
    const wrapper = mountPost({ can_edit: true })
    expect(clickButton(wrapper, 'Edit').exists()).toBe(true)
  })

  it('opens the edit form prefilled with the current body', async () => {
    const wrapper = mountPost({ can_edit: true, body: 'current text' })
    await clickButton(wrapper, 'Edit').trigger('click')
    expect((wrapper.find('textarea').element as HTMLTextAreaElement).value).toBe('current text')
  })

  it('shows the formatting toolbar only in edit mode', async () => {
    const wrapper = mountPost({ can_edit: true })
    expect(wrapper.find('button[title="Bold"]').exists()).toBe(false)
    await clickButton(wrapper, 'Edit').trigger('click')
    expect(wrapper.find('button[title="Bold"]').exists()).toBe(true)
  })

  it('saves an edit through useEditPost and closes the form', async () => {
    const wrapper = mountPost({ can_edit: true, body: 'old' })
    await clickButton(wrapper, 'Edit').trigger('click')
    await wrapper.find('textarea').setValue('  new text  ')
    await clickButton(wrapper, 'Edit').trigger('click')
    await flushPromises()

    expect(editPostMock).toHaveBeenCalledWith(101, 'new text')
    expect(wrapper.find('textarea').exists()).toBe(false)
  })

  it('cancels editing without calling the api', async () => {
    const wrapper = mountPost({ can_edit: true })
    await clickButton(wrapper, 'Edit').trigger('click')
    await clickButton(wrapper, 'Cancel').trigger('click')

    expect(editPostMock).not.toHaveBeenCalled()
    expect(wrapper.find('textarea').exists()).toBe(false)
  })

  it('reveals the original text in a popover on hover', async () => {
    usePostHistoryMock.mockReturnValue({
      data: ref({ post_id: 1, original_body: 'before edit', original_body_html: '<p>before edit</p>', edited_at: '' }),
    })
    const wrapper = mountPost({ is_edited: true })

    await wrapper.find('.edit-wrap').trigger('mouseenter')

    expect(wrapper.text()).toContain('before edit')
    expect(wrapper.text()).toContain('Original')

    await wrapper.find('.edit-wrap').trigger('mouseleave')
    expect(wrapper.text()).not.toContain('before edit')
  })

  it('reports the post through the inline report form', async () => {
    const wrapper = mountPost()

    await clickButton(wrapper, 'Report').trigger('click')
    await wrapper.find('input').setValue('  off-topic spam  ')
    await clickButton(wrapper, 'Send report').trigger('click')
    await flushPromises()

    expect(createReportMock).toHaveBeenCalledWith('b', 101, 'off-topic spam')
    expect(wrapper.find('input').exists()).toBe(false)
    expect(wrapper.text()).toContain('reported ✓')
  })

  it('sends a null reason when the report field is left empty', async () => {
    const wrapper = mountPost()

    await clickButton(wrapper, 'Report').trigger('click')
    await clickButton(wrapper, 'Send report').trigger('click')
    await flushPromises()

    expect(createReportMock).toHaveBeenCalledWith('b', 101, null)
  })

  it('cancels reporting without calling the api', async () => {
    const wrapper = mountPost()

    await clickButton(wrapper, 'Report').trigger('click')
    await clickButton(wrapper, 'Cancel').trigger('click')

    expect(createReportMock).not.toHaveBeenCalled()
    expect(wrapper.find('input').exists()).toBe(false)
  })

  it('shows the api detail when reporting fails', async () => {
    createReportMock.mockRejectedValue(new ApiError('too many reports, slow down', 429))
    const wrapper = mountPost()

    await clickButton(wrapper, 'Report').trigger('click')
    await clickButton(wrapper, 'Send report').trigger('click')
    await flushPromises()

    expect(wrapper.find('.text-danger').text()).toBe('too many reports, slow down')
    expect(wrapper.text()).not.toContain('reported ✓')
  })

  it('hides mod controls when not authenticated', () => {
    const wrapper = mountPost()
    expect(wrapper.text()).not.toContain('Delete')
  })

  it('deletes the post when authenticated', async () => {
    useAuthStore().login('jwt', 'admin')
    const wrapper = mountPost()
    await clickButton(wrapper, 'Delete').trigger('click')
    expect(removePostMock).toHaveBeenCalledWith(101)
  })

  it('bans the poster through the inline ban form', async () => {
    useAuthStore().login('jwt', 'admin')
    const wrapper = mountPost()

    await clickButton(wrapper, 'Ban').trigger('click')
    await wrapper.find('input').setValue('spam')
    await clickButton(wrapper, 'Confirm ban').trigger('click')
    await flushPromises()

    expect(banMock).toHaveBeenCalledWith(101, { reason: 'spam' })
  })

  it('shows the api detail when deleting fails', async () => {
    useAuthStore().login('jwt', 'admin')
    removePostMock.mockRejectedValue(new ApiError('post already deleted', 404))
    const wrapper = mountPost()

    await clickButton(wrapper, 'Delete').trigger('click')
    await flushPromises()

    expect(wrapper.find('.text-danger').text()).toBe('post already deleted')
  })

  it('shows a fallback message when banning fails without a detail', async () => {
    useAuthStore().login('jwt', 'admin')
    banMock.mockRejectedValue(new ApiError(null, 500))
    const wrapper = mountPost()

    await clickButton(wrapper, 'Ban').trigger('click')
    await clickButton(wrapper, 'Confirm ban').trigger('click')
    await flushPromises()

    expect(wrapper.find('.text-danger').text()).toBe('Failed to ban poster.')
  })
})
