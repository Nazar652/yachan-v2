import { describe, expect, it, vi, beforeEach } from 'vitest'
import { defineComponent, ref, type Ref } from 'vue'
import { mount, flushPromises } from '@vue/test-utils'
import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query'

import { usePostHistory } from '@/composables/usePostHistory'
import { getPostHistory } from '@/api/posts'

vi.mock('@/api/posts', () => ({
  getPostHistory: vi.fn(),
}))

const getPostHistoryMock = vi.mocked(getPostHistory)

beforeEach(() => getPostHistoryMock.mockReset())

function mountPostHistory(enabled: Ref<boolean>) {
  let api!: ReturnType<typeof usePostHistory>
  const Host = defineComponent({
    setup() {
      api = usePostHistory(ref('b'), 7, enabled)
      return () => null
    },
  })
  mount(Host, { global: { plugins: [[VueQueryPlugin, { queryClient: new QueryClient() }]] } })
  return api
}

describe('usePostHistory', () => {
  it('does not fetch while disabled', async () => {
    const api = mountPostHistory(ref(false))

    await flushPromises()

    expect(getPostHistoryMock).not.toHaveBeenCalled()
    expect(api.data.value).toBeUndefined()
  })

  it('fetches the original text once enabled', async () => {
    const edit = { post_id: 1, original_body: 'old', original_body_html: '<p>old</p>' }
    getPostHistoryMock.mockResolvedValue(edit as never)

    const api = mountPostHistory(ref(true))
    await flushPromises()

    expect(getPostHistoryMock).toHaveBeenCalledWith('b', 7)
    expect(api.data.value).toEqual(edit)
  })

  it('starts fetching when enabled flips true', async () => {
    getPostHistoryMock.mockResolvedValue(null as never)

    const enabled = ref(false)
    mountPostHistory(enabled)
    await flushPromises()
    expect(getPostHistoryMock).not.toHaveBeenCalled()

    enabled.value = true
    await flushPromises()

    expect(getPostHistoryMock).toHaveBeenCalledWith('b', 7)
  })
})
