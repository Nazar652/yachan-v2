import { describe, expect, it, vi } from 'vitest'
import { defineComponent, ref } from 'vue'
import { mount } from '@vue/test-utils'
import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query'

import { useCaptcha, CAPTCHA_QUERY_KEY } from '@/composables/useCaptcha'
import { fetchCaptcha } from '@/api/captcha'

vi.mock('@/api/captcha', () => ({
  fetchCaptcha: vi.fn(),
}))

function mountWithQuery(setup: () => unknown) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  const Host = defineComponent({
    setup() {
      setup()
      return () => null
    },
  })
  mount(Host, { global: { plugins: [[VueQueryPlugin, { queryClient }]] } })
  return queryClient
}

async function flushQueries() {
  await new Promise((resolve) => setTimeout(resolve, 0))
}

describe('useCaptcha', () => {
  it('fetches a challenge into the canonical query key by default', async () => {
    const challenge = { token: 'tok', image_base64_light: 'a==', image_base64_dark: 'b==' }
    vi.mocked(fetchCaptcha).mockResolvedValue(challenge)

    const queryClient = mountWithQuery(() => useCaptcha())
    await flushQueries()

    expect(queryClient.getQueryData(CAPTCHA_QUERY_KEY)).toBe(challenge)
    expect(fetchCaptcha).toHaveBeenCalledOnce()
  })

  it('does not fetch when disabled, e.g. for an admin poster', async () => {
    vi.mocked(fetchCaptcha).mockReset()
    vi.mocked(fetchCaptcha).mockResolvedValue({ token: 'tok', image_base64_light: 'a==', image_base64_dark: 'b==' })

    mountWithQuery(() => useCaptcha(ref(false)))
    await flushQueries()

    expect(fetchCaptcha).not.toHaveBeenCalled()
  })
})
