import { describe, expect, it, vi, beforeEach } from 'vitest'

import { apiClient } from '@/api/client'
import { listThreads } from '@/api/threads'

vi.mock('@/api/client', () => ({
  apiClient: { GET: vi.fn() },
}))

const getMock = vi.mocked(apiClient.GET)

describe('listThreads', () => {
  beforeEach(() => getMock.mockReset())

  it('returns the data on success', async () => {
    const threads = [{ id: 1, board_id: 1, title: 'hello', is_locked: false, is_sticky: false, reply_count: 0, bump_at: '', created_at: '' }]
    getMock.mockResolvedValue({ data: threads, error: undefined })

    await expect(listThreads('b')).resolves.toBe(threads)
    expect(getMock).toHaveBeenCalledWith('/api/{board_slug}/threads', {
      params: { path: { board_slug: 'b' } },
    })
  })

  it('throws when the client returns an error', async () => {
    const error = { detail: 'not found' }
    getMock.mockResolvedValue({ data: undefined, error })

    await expect(listThreads('b')).rejects.toBe(error)
  })
})

