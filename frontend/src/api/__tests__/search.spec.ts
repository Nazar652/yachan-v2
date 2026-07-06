import { describe, expect, it, vi, beforeEach } from 'vitest'

import { apiClient } from '@/api/client'
import { getSimilarThreads, getSimilarThreadsForText, searchPosts } from '@/api/search'

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

describe('getSimilarThreads', () => {
  beforeEach(() => getMock.mockReset())

  it('returns similar threads for the given board and thread', async () => {
    const results = [
      {
        board_slug: 'b', thread_id: 2, title: 'other thread', op_snippet: 'snippet',
        thumbnail_url: null, reply_count: 3, score: 0.8,
      },
    ]
    getMock.mockResolvedValue({ data: results, error: undefined })

    await expect(getSimilarThreads('b', 1)).resolves.toBe(results)
    expect(getMock).toHaveBeenCalledWith('/api/{board_slug}/threads/{thread_id}/similar', {
      params: { path: { board_slug: 'b', thread_id: 1 } },
    })
  })

  it('throws when the client returns an error', async () => {
    const error = { detail: 'boom' }
    getMock.mockResolvedValue({ data: undefined, error })

    await expect(getSimilarThreads('b', 1)).rejects.toMatchObject(error)
  })
})

describe('getSimilarThreadsForText', () => {
  beforeEach(() => getMock.mockReset())

  it('returns similar threads for the given board and text', async () => {
    const results = [
      {
        board_slug: 'b', thread_id: 3, title: 'duplicate?', op_snippet: 'snippet',
        thumbnail_url: null, reply_count: 0, score: 0.9,
      },
    ]
    getMock.mockResolvedValue({ data: results, error: undefined })

    await expect(getSimilarThreadsForText('b', 'is this a duplicate thread')).resolves.toBe(results)
    expect(getMock).toHaveBeenCalledWith('/api/{board_slug}/threads/similar', {
      params: { path: { board_slug: 'b' }, query: { q: 'is this a duplicate thread' } },
    })
  })

  it('throws when the client returns an error', async () => {
    const error = { detail: 'boom' }
    getMock.mockResolvedValue({ data: undefined, error })

    await expect(getSimilarThreadsForText('b', 'text')).rejects.toMatchObject(error)
  })
})
