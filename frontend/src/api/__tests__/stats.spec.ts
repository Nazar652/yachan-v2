import { describe, expect, it, vi, beforeEach } from 'vitest'

import { apiClient } from '@/api/client'
import { fetchSiteStats } from '@/api/stats'

vi.mock('@/api/client', () => ({
  apiClient: { GET: vi.fn() },
}))

const getMock = vi.mocked(apiClient.GET)

describe('fetchSiteStats', () => {
  beforeEach(() => getMock.mockReset())

  it('returns the data on success', async () => {
    const stats = { board_count: 4, thread_count: 127, post_count: 2400, online_count: 38, boards: [] }
    getMock.mockResolvedValue({ data: stats, error: undefined })

    await expect(fetchSiteStats()).resolves.toBe(stats)
    expect(getMock).toHaveBeenCalledWith('/api/stats')
  })

  it('throws when the client returns an error', async () => {
    const error = { detail: 'boom' }
    getMock.mockResolvedValue({ data: undefined, error })

    await expect(fetchSiteStats()).rejects.toBe(error)
  })
})
