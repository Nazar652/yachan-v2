import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { defineComponent, ref } from 'vue'
import { mount } from '@vue/test-utils'
import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query'

import { useDuplicateThreads, duplicateThreadsQueryKey } from '@/composables/useDuplicateThreads'
import { getSimilarThreadsForText } from '@/api/search'

vi.mock('@/api/search', () => ({
  getSimilarThreadsForText: vi.fn(),
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

describe('duplicateThreadsQueryKey', () => {
  it('builds a stable key from slug and text', () => {
    expect(duplicateThreadsQueryKey('b', 'hello')).toEqual(['duplicate-threads', 'b', 'hello'])
  })
})

describe('useDuplicateThreads', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.mocked(getSimilarThreadsForText).mockReset()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('does not fetch before the debounce delay elapses', async () => {
    vi.mocked(getSimilarThreadsForText).mockResolvedValue([])
    const text = ref('')

    mountWithQuery(() => useDuplicateThreads(ref('b'), text))
    text.value = 'a sufficiently long draft body'
    await vi.advanceTimersByTimeAsync(300)

    expect(getSimilarThreadsForText).not.toHaveBeenCalled()
  })

  it('fetches after the debounce delay once the text is long enough', async () => {
    const results = [
      {
        board_slug: 'b', thread_id: 4, title: 't', op_snippet: null,
        thumbnail_url: null, reply_count: 0, score: 0.5,
      },
    ]
    vi.mocked(getSimilarThreadsForText).mockResolvedValue(results)
    const text = ref('')

    const queryClient = mountWithQuery(() => useDuplicateThreads(ref('b'), text))
    text.value = 'a sufficiently long draft body'
    await vi.advanceTimersByTimeAsync(600)

    expect(getSimilarThreadsForText).toHaveBeenCalledWith('b', 'a sufficiently long draft body')
    expect(
      queryClient.getQueryData(duplicateThreadsQueryKey('b', 'a sufficiently long draft body')),
    ).toBe(results)
  })

  it('does not fetch when the debounced text is still too short', async () => {
    vi.mocked(getSimilarThreadsForText).mockResolvedValue([])
    const text = ref('short')

    mountWithQuery(() => useDuplicateThreads(ref('b'), text))
    await vi.advanceTimersByTimeAsync(600)

    expect(getSimilarThreadsForText).not.toHaveBeenCalled()
  })

  it('resets the debounce timer on rapid changes', async () => {
    const results = [
      {
        board_slug: 'b', thread_id: 5, title: 't', op_snippet: null,
        thumbnail_url: null, reply_count: 0, score: 0.5,
      },
    ]
    vi.mocked(getSimilarThreadsForText).mockResolvedValue(results)
    const text = ref('initial long enough draft text')

    mountWithQuery(() => useDuplicateThreads(ref('b'), text))
    await vi.advanceTimersByTimeAsync(400)
    text.value = 'updated long enough draft text too'
    await vi.advanceTimersByTimeAsync(400)

    expect(getSimilarThreadsForText).not.toHaveBeenCalled()

    await vi.advanceTimersByTimeAsync(300)

    expect(getSimilarThreadsForText).toHaveBeenCalledWith('b', 'updated long enough draft text too')
    expect(getSimilarThreadsForText).toHaveBeenCalledTimes(1)
  })
})
