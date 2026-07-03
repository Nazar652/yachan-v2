import { describe, expect, it, vi, beforeEach } from 'vitest'
import { ref } from 'vue'
import { mount } from '@vue/test-utils'

import SearchView from '@/views/SearchView.vue'
import { useSearch } from '@/composables/useSearch'

vi.mock('@/composables/useSearch', () => ({
  useSearch: vi.fn(),
}))

const routeMock = { query: {} as Record<string, string> }

vi.mock('vue-router', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue-router')>()
  return {
    ...actual,
    useRoute: () => routeMock,
    useRouter: () => ({ replace: vi.fn() }),
    RouterLink: { props: ['to'], template: '<a :href="to"><slot /></a>' },
  }
})

const useSearchMock = vi.mocked(useSearch)

function stub(data: unknown, extra: Record<string, unknown> = {}) {
  useSearchMock.mockReturnValue({
    data: ref(data),
    isFetching: ref(false),
    isError: ref(false),
    ...extra,
  } as unknown as ReturnType<typeof useSearch>)
}

beforeEach(() => {
  routeMock.query = {}
  useSearchMock.mockReset()
  stub(undefined)
})

describe('SearchView', () => {
  it('prompts for input when there is no query', () => {
    const wrapper = mount(SearchView)
    expect(wrapper.text()).toContain('Type at least two characters')
  })

  it('renders matching posts', () => {
    routeMock.query = { q: 'cats' }
    stub([
      { board_slug: 'b', thread_id: 7, post_number: 42, is_op: true, name: 'Anon', body: 'a cat sat', body_html: null, created_at: '2026-01-01T00:00:00Z', score: 0.88 },
    ])
    const wrapper = mount(SearchView)
    expect(wrapper.text()).toContain('a cat sat')
    expect(wrapper.text()).toContain('/b/')
    expect(wrapper.text()).toContain('No.42')
    expect(wrapper.find('a').attributes('href')).toBe('/b/thread/7#post-42')
  })

  it('shows an empty state when nothing matches', () => {
    routeMock.query = { q: 'zzz' }
    stub([])
    const wrapper = mount(SearchView)
    expect(wrapper.text()).toContain('No posts match')
  })
})
