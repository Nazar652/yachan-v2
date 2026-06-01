import { describe, expect, it, vi, beforeEach } from 'vitest'

import { apiClient } from '@/api/client'
import { listThreads, getThread, createThread } from '@/api/threads'

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

describe('getThread', () => {
  beforeEach(() => getMock.mockReset())

  it('returns the thread detail on success', async () => {
    const thread = { id: 42, board_id: 1, title: 'Test', is_locked: false, is_sticky: false, reply_count: 3, bump_at: '', created_at: '', posts: [] }
    getMock.mockResolvedValue({ data: thread, error: undefined })

    await expect(getThread('b', 42)).resolves.toBe(thread)
    expect(getMock).toHaveBeenCalledWith('/api/{board_slug}/threads/{thread_id}', {
      params: { path: { board_slug: 'b', thread_id: 42 } },
    })
  })

  it('throws when the client returns an error', async () => {
    const error = { detail: 'not found' }
    getMock.mockResolvedValue({ data: undefined, error })

    await expect(getThread('b', 42)).rejects.toBe(error)
  })
})

describe('createThread', () => {
  const fetchMock = vi.fn()
  beforeEach(() => {
    fetchMock.mockReset()
    vi.stubGlobal('fetch', fetchMock)
  })

  it('posts multipart form data and returns the thread on success', async () => {
    const thread = { id: 1, board_id: 1, title: 'T', is_locked: false, is_sticky: false, reply_count: 0, bump_at: '', created_at: '', posts: [] }
    fetchMock.mockResolvedValue({ ok: true, json: () => Promise.resolve(thread) })

    const file = new File(['img'], 'photo.jpg', { type: 'image/jpeg' })
    const result = await createThread('b', { title: 'T', body: 'Hi' }, [file], 'tok', 'ans')

    expect(result).toBe(thread)
    expect(fetchMock).toHaveBeenCalledOnce()

    const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toContain('/api/b/threads')
    expect(options.method).toBe('POST')
    expect((options.headers as Record<string, string>)['X-Captcha-Token']).toBe('tok')
    expect((options.headers as Record<string, string>)['X-Captcha-Answer']).toBe('ans')
    expect(options.body).toBeInstanceOf(FormData)
  })

  it('throws the parsed error body when response is not ok', async () => {
    const error = { detail: 'bad captcha' }
    fetchMock.mockResolvedValue({ ok: false, json: () => Promise.resolve(error), statusText: 'Bad Request' })

    await expect(createThread('b', {}, [], 'tok', 'wrong')).rejects.toEqual(error)
  })
})

