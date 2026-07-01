import { describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'
import { mount } from '@vue/test-utils'

import CreateThreadView from '@/views/CreateThreadView.vue'
import { useCaptcha } from '@/composables/useCaptcha'

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

function stubCaptcha(overrides: Record<string, unknown> = {}) {
  useCaptchaMock.mockReturnValue({
    data: ref({ token: 'tok', image_base64_light: 'abc==', image_base64_dark: 'def==' }),
    isPending: ref(false),
    isError: ref(false),
    refetch: vi.fn(),
    ...overrides,
  } as unknown as ReturnType<typeof useCaptcha>)
}

describe('CreateThreadView', () => {
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
})

