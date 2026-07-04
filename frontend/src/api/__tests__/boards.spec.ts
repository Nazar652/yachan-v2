import { describe, expect, it, vi, beforeEach } from 'vitest'

import { apiClient } from '@/api/client'
import { getBoard, listBoards } from '@/api/boards'

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

    await expect(listBoards()).rejects.toMatchObject(error)
  })
})

describe('getBoard', () => {
  beforeEach(() => getMock.mockReset())

  it('returns the board on success', async () => {
    const board = { id: 1, slug: 'b', title: 'Random' }
    getMock.mockResolvedValue({ data: board, error: undefined })

    await expect(getBoard('b')).resolves.toBe(board)
    expect(getMock).toHaveBeenCalledWith('/api/boards/{slug}', { params: { path: { slug: 'b' } } })
  })

  it('throws when the client returns an error', async () => {
    const error = { detail: 'board not found' }
    getMock.mockResolvedValue({ data: undefined, error })

    await expect(getBoard('nope')).rejects.toMatchObject(error)
  })
})
