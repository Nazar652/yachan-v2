import { describe, expect, it, vi, beforeEach } from 'vitest'
import { ref } from 'vue'
import { mount, flushPromises } from '@vue/test-utils'

import ReplyForm from '@/components/ReplyForm.vue'
import { useCaptcha } from '@/composables/useCaptcha'
import { createReply } from '@/api/threads'

const setQueryDataMock = vi.fn()
vi.mock('@tanstack/vue-query', () => ({
  useQueryClient: () => ({ setQueryData: setQueryDataMock }),
}))

vi.mock('@/composables/useCaptcha', () => ({
  useCaptcha: vi.fn(),
}))

vi.mock('@/api/threads', () => ({
  createReply: vi.fn(),
}))

// stub child UI components; CaptchaWidget forwards v-model so the captcha
// answer can be set from a test by typing into its input
const globalStubs = {
  BaseButton: { template: '<button :type="type" @click="$emit(\'click\')"><slot /></button>', props: ['type'], emits: ['click'] },
  BaseInput: { template: '<input />' },
  CaptchaWidget: {
    template: '<input class="captcha-input" @input="$emit(\'update:modelValue\', $event.target.value)" />',
    emits: ['update:modelValue', 'refresh'],
  },
}

const useCaptchaMock = vi.mocked(useCaptcha)
const createReplyMock = vi.mocked(createReply)
const refetchMock = vi.fn()

function stubCaptcha(overrides: Record<string, unknown> = {}) {
  useCaptchaMock.mockReturnValue({
    data: ref({ token: 'tok', image_base64: 'abc==' }),
    isPending: ref(false),
    isError: ref(false),
    refetch: refetchMock,
    ...overrides,
  } as unknown as ReturnType<typeof useCaptcha>)
}

function mountForm() {
  return mount(ReplyForm, {
    props: { slug: 'b', threadId: 42 },
    global: { stubs: globalStubs },
  })
}

describe('ReplyForm', () => {
  beforeEach(() => {
    setQueryDataMock.mockReset()
    createReplyMock.mockReset()
    refetchMock.mockReset()
    stubCaptcha()
  })

  it('renders the reply heading', () => {
    const wrapper = mountForm()
    expect(wrapper.text()).toContain('Reply')
  })

  it('renders the captcha widget', () => {
    const wrapper = mountForm()
    expect(wrapper.find('.captcha-input').exists()).toBe(true)
  })

  it('renders the formatting toolbar above the body field', () => {
    const wrapper = mountForm()
    expect(wrapper.find('button[title="Bold"]').exists()).toBe(true)
    expect(wrapper.find('button[title="Spoiler"]').exists()).toBe(true)
  })

  it('shows an error and does not submit when body and files are empty', async () => {
    const wrapper = mountForm()
    await wrapper.find('form').trigger('submit')
    expect(wrapper.text()).toContain('A reply needs a body or a file')
    expect(createReplyMock).not.toHaveBeenCalled()
  })

  it('requires a captcha answer before submitting', async () => {
    const wrapper = mountForm()
    await wrapper.find('#reply-body').setValue('hello')
    await wrapper.find('form').trigger('submit')
    expect(wrapper.text()).toContain('captcha answer')
    expect(createReplyMock).not.toHaveBeenCalled()
  })

  it('posts the reply and appends it to the thread cache on success', async () => {
    const post = { id: 7, post_number: 102, name: 'Anon' }
    createReplyMock.mockResolvedValue(post as never)

    const wrapper = mountForm()
    await wrapper.find('#reply-body').setValue('hello')
    await wrapper.find('.captcha-input').setValue('ans')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(createReplyMock).toHaveBeenCalledWith(
      'b',
      42,
      { name: undefined, body: 'hello', sage: false },
      [],
      'tok',
      'ans',
    )
    expect(setQueryDataMock).toHaveBeenCalledOnce()
    expect(refetchMock).toHaveBeenCalled()
    // form is reset after a successful post
    expect((wrapper.find('#reply-body').element as HTMLTextAreaElement).value).toBe('')
  })

  it('appends the new post to existing posts via the cache updater', async () => {
    createReplyMock.mockResolvedValue({ id: 7, post_number: 102 } as never)

    const wrapper = mountForm()
    await wrapper.find('#reply-body').setValue('hello')
    await wrapper.find('.captcha-input').setValue('ans')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const [, updater] = setQueryDataMock.mock.calls[0] as [unknown, (old: unknown) => unknown]
    const existing = { id: 42, reply_count: 1, posts: [{ id: 1, post_number: 1 }] }
    expect(updater(existing)).toEqual({
      id: 42,
      reply_count: 2,
      posts: [{ id: 1, post_number: 1 }, { id: 7, post_number: 102 }],
    })
    expect(updater(undefined)).toBeUndefined()
  })
})
