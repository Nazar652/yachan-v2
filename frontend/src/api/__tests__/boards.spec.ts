import { describe, expect, it, vi, beforeEach } from 'vitest'

import { apiClient } from '@/api/client'
import { listBoards } from '@/api/boards'

vi.mock('@/api/client', () => ({
  apiClient: { GET: vi.fn() },
}))

const getMock = vi.mocked(apiClient.GET)

describe('listBoards', () => {
  beforeEach(() => getMock.mockReset())

  it('returns the data on success', async () => {
    const boards = [{ id: 1, slug: 'b', title: 'Random' }]
    getMock.mockResolvedValue({ data: boards, error: undefined })

    await expect(listBoards()).resolves.toBe(boards)
    expect(getMock).toHaveBeenCalledWith('/api/boards')
  })

  it('throws when the client returns an error', async () => {
    const error = { detail: 'boom' }
    getMock.mockResolvedValue({ data: undefined, error })

    await expect(listBoards()).rejects.toBe(error)
  })
})
