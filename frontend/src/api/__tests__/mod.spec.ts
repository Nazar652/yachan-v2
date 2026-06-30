import { describe, expect, it, vi, beforeEach } from 'vitest'

import { apiClient } from '@/api/client'
import {
  modLogin,
  listReports,
  resolveReport,
  deletePost,
  setThreadLocked,
  setThreadSticky,
  banPoster,
  createBoard,
  updateBoard,
  reorderBoards,
} from '@/api/mod'

vi.mock('@/api/client', () => ({
  apiClient: { GET: vi.fn(), POST: vi.fn(), DELETE: vi.fn(), PATCH: vi.fn(), PUT: vi.fn() },
}))

const getMock = vi.mocked(apiClient.GET)
const postMock = vi.mocked(apiClient.POST)
const deleteMock = vi.mocked(apiClient.DELETE)
const patchMock = vi.mocked(apiClient.PATCH)
const putMock = vi.mocked(apiClient.PUT)

describe('modLogin', () => {
  beforeEach(() => postMock.mockReset())

  it('returns the token on success', async () => {
    const token = { access_token: 'jwt', token_type: 'bearer' }
    postMock.mockResolvedValue({ data: token, error: undefined })

    await expect(modLogin('admin', 'pw')).resolves.toBe(token)
    expect(postMock).toHaveBeenCalledWith('/api/mod/login', {
      body: { username: 'admin', password: 'pw' },
    })
  })

  it('throws when the client returns an error', async () => {
    const error = { detail: 'bad credentials' }
    postMock.mockResolvedValue({ data: undefined, error })

    await expect(modLogin('admin', 'wrong')).rejects.toMatchObject(error)
  })
})

describe('createBoard', () => {
  beforeEach(() => postMock.mockReset())

  it('creates a board and returns it', async () => {
    const board = { id: 1, slug: 'b', title: 'Random', description: null, bump_limit: 300, is_active: true, created_at: '' }
    postMock.mockResolvedValue({ data: board, error: undefined })

    const payload = { slug: 'b', title: 'Random', bump_limit: 300 }
    await expect(createBoard(payload)).resolves.toBe(board)
    expect(postMock).toHaveBeenCalledWith('/api/mod/boards', { body: payload })
  })

  it('throws when the client returns an error', async () => {
    const error = { detail: 'admin privileges required' }
    postMock.mockResolvedValue({ data: undefined, error })

    await expect(createBoard({ slug: 'b', title: 'x', bump_limit: 300 })).rejects.toMatchObject(error)
  })
})

describe('updateBoard', () => {
  beforeEach(() => patchMock.mockReset())

  it('updates a board and returns it', async () => {
    const board = { id: 1, slug: 'b', title: 'New', description: null, bump_limit: 300, is_active: false, created_at: '' }
    patchMock.mockResolvedValue({ data: board, error: undefined } as never)

    await expect(updateBoard('b', { title: 'New', is_active: false })).resolves.toBe(board)
    expect(patchMock).toHaveBeenCalledWith('/api/mod/boards/{board_slug}', {
      params: { path: { board_slug: 'b' } },
      body: { title: 'New', is_active: false },
    })
  })

  it('throws when the client returns an error', async () => {
    const error = { detail: 'not found' }
    patchMock.mockResolvedValue({ data: undefined, error } as never)

    await expect(updateBoard('b', { title: 'x' })).rejects.toMatchObject(error)
  })
})

describe('reorderBoards', () => {
  beforeEach(() => putMock.mockReset())

  it('reorders boards and returns the new order', async () => {
    const boards = [
      { id: 2, slug: 'g', title: 'Games', description: null, bump_limit: 300, is_active: true, position: 0, created_at: '' },
      { id: 1, slug: 'b', title: 'Random', description: null, bump_limit: 300, is_active: true, position: 1, created_at: '' },
    ]
    putMock.mockResolvedValue({ data: boards, error: undefined } as never)

    await expect(reorderBoards(['g', 'b'])).resolves.toBe(boards)
    expect(putMock).toHaveBeenCalledWith('/api/mod/boards/order', { body: { slugs: ['g', 'b'] } })
  })

  it('throws when the client returns an error', async () => {
    const error = { detail: 'admin privileges required' }
    putMock.mockResolvedValue({ data: undefined, error } as never)

    await expect(reorderBoards(['g', 'b'])).rejects.toMatchObject(error)
  })
})

describe('listReports', () => {
  beforeEach(() => getMock.mockReset())

  it('returns the reports on success', async () => {
    const reports = [{ id: 1, post_id: 5, board_id: 1, reason: 'spam', is_resolved: false, created_at: '' }]
    getMock.mockResolvedValue({ data: reports, error: undefined })

    await expect(listReports()).resolves.toBe(reports)
    expect(getMock).toHaveBeenCalledWith('/api/mod/reports')
  })

  it('throws when the client returns an error', async () => {
    const error = { detail: 'unauthorized' }
    getMock.mockResolvedValue({ data: undefined, error })

    await expect(listReports()).rejects.toMatchObject(error)
  })
})

describe('resolveReport', () => {
  beforeEach(() => postMock.mockReset())

  it('resolves the report and returns nothing on success', async () => {
    postMock.mockResolvedValue({ data: undefined, error: undefined })

    await expect(resolveReport(7)).resolves.toBeUndefined()
    expect(postMock).toHaveBeenCalledWith('/api/mod/reports/{report_id}/resolve', {
      params: { path: { report_id: 7 } },
    })
  })

  it('throws when the client returns an error', async () => {
    const error = { detail: 'not found' }
    postMock.mockResolvedValue({ data: undefined, error })

    await expect(resolveReport(7)).rejects.toMatchObject(error)
  })
})

describe('deletePost', () => {
  beforeEach(() => deleteMock.mockReset())

  it('deletes the post on success', async () => {
    deleteMock.mockResolvedValue({ data: undefined, error: undefined } as never)

    await expect(deletePost('b', 101)).resolves.toBeUndefined()
    expect(deleteMock).toHaveBeenCalledWith('/api/mod/{board_slug}/posts/{post_number}', {
      params: { path: { board_slug: 'b', post_number: 101 } },
    })
  })

  it('throws when the client returns an error', async () => {
    const error = { detail: 'forbidden' }
    deleteMock.mockResolvedValue({ data: undefined, error } as never)

    await expect(deletePost('b', 101)).rejects.toMatchObject(error)
  })
})

describe('setThreadLocked', () => {
  beforeEach(() => postMock.mockReset())

  it('locks a thread via the locked query param', async () => {
    postMock.mockResolvedValue({ data: undefined, error: undefined })

    await expect(setThreadLocked('b', 42, true)).resolves.toBeUndefined()
    expect(postMock).toHaveBeenCalledWith('/api/mod/{board_slug}/threads/{thread_id}/lock', {
      params: { path: { board_slug: 'b', thread_id: 42 }, query: { locked: true } },
    })
  })

  it('throws when the client returns an error', async () => {
    const error = { detail: 'forbidden' }
    postMock.mockResolvedValue({ data: undefined, error })

    await expect(setThreadLocked('b', 42, false)).rejects.toMatchObject(error)
  })
})

describe('setThreadSticky', () => {
  beforeEach(() => postMock.mockReset())

  it('stickies a thread via the sticky query param', async () => {
    postMock.mockResolvedValue({ data: undefined, error: undefined })

    await expect(setThreadSticky('b', 42, true)).resolves.toBeUndefined()
    expect(postMock).toHaveBeenCalledWith('/api/mod/{board_slug}/threads/{thread_id}/sticky', {
      params: { path: { board_slug: 'b', thread_id: 42 }, query: { sticky: true } },
    })
  })

  it('throws when the client returns an error', async () => {
    const error = { detail: 'forbidden' }
    postMock.mockResolvedValue({ data: undefined, error })

    await expect(setThreadSticky('b', 42, true)).rejects.toMatchObject(error)
  })
})

describe('banPoster', () => {
  beforeEach(() => postMock.mockReset())

  it('bans the poster and returns the ban on success', async () => {
    const ban = { id: 1, ip_hash: 'h', board_id: null, reason: 'spam', expires_at: null, is_active: true, created_at: '' }
    postMock.mockResolvedValue({ data: ban, error: undefined })

    await expect(banPoster('b', 101, { reason: 'spam' })).resolves.toBe(ban)
    expect(postMock).toHaveBeenCalledWith('/api/mod/{board_slug}/posts/{post_number}/ban', {
      params: { path: { board_slug: 'b', post_number: 101 } },
      body: { reason: 'spam' },
    })
  })

  it('throws when the client returns an error', async () => {
    const error = { detail: 'forbidden' }
    postMock.mockResolvedValue({ data: undefined, error })

    await expect(banPoster('b', 101, { reason: 'spam' })).rejects.toMatchObject(error)
  })
})
