import { describe, expect, it, vi, beforeEach } from 'vitest'

import { apiClient } from '@/api/client'
import { searchPosts } from '@/api/search'

vi.mock('@/api/client', () => ({
  apiClient: { GET: vi.fn() },
}))

const getMock = vi.mocked(apiClient.GET)

describe('searchPosts', () => {
  beforeEach(() => getMock.mockReset())

  it('returns results and forwards the query params', async () => {
    const results = [
      {
        board_slug: 'b', thread_id: 1, post_number: 2, is_op: false,
        name: 'Anon', body: 'cats', body_html: null, created_at: '', score: 0.9,
      },
    ]
    getMock.mockResolvedValue({ data: results, error: undefined })

    await expect(searchPosts('cats', 'b', 10)).resolves.toBe(results)
    expect(getMock).toHaveBeenCalledWith('/api/search', {
      params: { query: { q: 'cats', board: 'b', limit: 10 } },
    })
  })

  it('omits the board and defaults the limit', async () => {
    getMock.mockResolvedValue({ data: [], error: undefined })

    await searchPosts('cats')
    expect(getMock).toHaveBeenCalledWith('/api/search', {
      params: { query: { q: 'cats', board: undefined, limit: 20 } },
    })
  })

  it('throws when the client returns an error', async () => {
    const error = { detail: 'boom' }
    getMock.mockResolvedValue({ data: undefined, error })

    await expect(searchPosts('cats')).rejects.toMatchObject(error)
  })
})
