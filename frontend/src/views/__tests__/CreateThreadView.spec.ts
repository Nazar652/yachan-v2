import { describe, expect, it, vi, beforeEach } from 'vitest'
import { ref } from 'vue'
import { mount, flushPromises, type VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

import CreateThreadView from '@/views/CreateThreadView.vue'
import { useCaptcha } from '@/composables/useCaptcha'
import { useDuplicateThreads } from '@/composables/useDuplicateThreads'
import { createThread } from '@/api/threads'
import { useAuthStore } from '@/stores/auth'

vi.mock('vue-router', () => ({
  useRoute: () => ({ params: { slug: 'b' } }),
  useRouter: () => ({ push: vi.fn() }),
  RouterLink: { template: '<a><slot /></a>' },
}))

vi.mock('@tanstack/vue-query', () => ({
  useQueryClient: () => ({ invalidateQueries: vi.fn() }),
}))

vi.mock('@/composables/useCaptcha', () => ({
  useCaptcha: vi.fn(),
}))

vi.mock('@/composables/useDuplicateThreads', () => ({
  useDuplicateThreads: vi.fn(),
}))

vi.mock('@/api/threads', () => ({
  createThread: vi.fn(),
}))

// stub all child UI components so the form structure is testable without styles
const globalStubs = {
  RouterLink: { template: '<a><slot /></a>' },
  BaseButton: { template: '<button type="button" @click="$emit(\'click\')"><slot /></button>' },
  BaseInput: { template: '<input />' },
  CaptchaWidget: { template: '<div data-testid="captcha" />' },
}

const useCaptchaMock = vi.mocked(useCaptcha)
const useDuplicateThreadsMock = vi.mocked(useDuplicateThreads)

function stubCaptcha(overrides: Record<string, unknown> = {}) {
  useCaptchaMock.mockReturnValue({
    data: ref({ token: 'tok', image_base64_light: 'abc==', image_base64_dark: 'def==' }),
    isPending: ref(false),
    isError: ref(false),
    refetch: vi.fn(),
    ...overrides,
  } as unknown as ReturnType<typeof useCaptcha>)
}

function stubDuplicateThreads(items: unknown[] = []) {
  useDuplicateThreadsMock.mockReturnValue({
    data: ref(items),
  } as unknown as ReturnType<typeof useDuplicateThreads>)
}

async function selectImage(wrapper: VueWrapper) {
  const input = wrapper.find('#files')
  const file = new File(['img'], 'photo.jpg', { type: 'image/jpeg' })
  Object.defineProperty(input.element, 'files', { value: [file] })
  await input.trigger('change')
}

describe('CreateThreadView', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    stubDuplicateThreads()
  })

  it('renders the form heading', () => {
    stubCaptcha()
    const wrapper = mount(CreateThreadView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('New thread')
  })

  it('shows the board slug in the back link', () => {
    stubCaptcha()
    const wrapper = mount(CreateThreadView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('/b/')
  })

  it('shows an error when submitting without an image', async () => {
    stubCaptcha()
    const wrapper = mount(CreateThreadView, { global: { stubs: globalStubs } })
    await wrapper.find('form').trigger('submit')
    expect(wrapper.text()).toContain('image')
  })

  it('renders the captcha widget', () => {
    stubCaptcha()
    const wrapper = mount(CreateThreadView, { global: { stubs: globalStubs } })
    expect(wrapper.find('[data-testid="captcha"]').exists()).toBe(true)
  })

  it('renders the formatting toolbar above the body field', () => {
    stubCaptcha()
    const wrapper = mount(CreateThreadView, { global: { stubs: globalStubs } })
    expect(wrapper.find('button[title="Bold"]').exists()).toBe(true)
    expect(wrapper.find('button[title="Quote"]').exists()).toBe(true)
  })

  it('hides the captcha widget for an admin poster', () => {
    stubCaptcha()
    useAuthStore().login('admin-jwt', 'admin')
    const wrapper = mount(CreateThreadView, { global: { stubs: globalStubs } })
    expect(wrapper.find('[data-testid="captcha"]').exists()).toBe(false)
  })

  it('posts as admin without a captcha answer, sending the bearer token', async () => {
    stubCaptcha()
    useAuthStore().login('admin-jwt', 'admin')
    vi.mocked(createThread).mockResolvedValue({ id: 1, posts: [{ post_number: 1 }] } as never)

    const wrapper = mount(CreateThreadView, { global: { stubs: globalStubs } })
    await selectImage(wrapper)
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(createThread).toHaveBeenCalledWith(
      'b',
      { title: undefined, name: undefined, body: undefined },
      [expect.any(File)],
      null,
      null,
      'admin-jwt',
    )
  })

  it('shows the duplicate-thread hint when matches are found', () => {
    stubCaptcha()
    stubDuplicateThreads([
      {
        board_slug: 'b', thread_id: 9, title: 'existing discussion', op_snippet: null,
        thumbnail_url: null, reply_count: 4, score: 0.9,
      },
    ])
    const wrapper = mount(CreateThreadView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).toContain('Possibly already being discussed')
    expect(wrapper.text()).toContain('existing discussion')
  })

  it('hides the duplicate-thread hint when there are no matches', () => {
    stubCaptcha()
    stubDuplicateThreads([])
    const wrapper = mount(CreateThreadView, { global: { stubs: globalStubs } })
    expect(wrapper.text()).not.toContain('Possibly already being discussed')
  })
})

