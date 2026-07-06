import { describe, expect, it, vi, beforeEach } from 'vitest'

import { apiClient } from '@/api/client'
import {
  listThreads,
  listLatestThreads,
  getThread,
  getThreadStatuses,
  createThread,
  createReply,
} from '@/api/threads'

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
      params: { path: { board_slug: 'b' }, query: { limit: 50, offset: 0 } },
    })
  })

  it('passes the page window through as limit and offset', async () => {
    getMock.mockResolvedValue({ data: [], error: undefined })

    await listThreads('b', 10, 20)
    expect(getMock).toHaveBeenCalledWith('/api/{board_slug}/threads', {
      params: { path: { board_slug: 'b' }, query: { limit: 10, offset: 20 } },
    })
  })

  it('throws when the client returns an error', async () => {
    const error = { detail: 'not found' }
    getMock.mockResolvedValue({ data: undefined, error })

    await expect(listThreads('b')).rejects.toMatchObject(error)
  })
})

describe('listLatestThreads', () => {
  beforeEach(() => getMock.mockReset())

  it('returns the data on success', async () => {
    const latest = [{ id: 1, board_slug: 'b', title: 'hello', reply_count: 2, bump_at: '', created_at: '' }]
    getMock.mockResolvedValue({ data: latest, error: undefined })

    await expect(listLatestThreads()).resolves.toBe(latest)
    expect(getMock).toHaveBeenCalledWith('/api/threads/latest', {
      params: { query: { limit: 5 } },
    })
  })

  it('throws when the client returns an error', async () => {
    const error = { detail: 'boom' }
    getMock.mockResolvedValue({ data: undefined, error })

    await expect(listLatestThreads()).rejects.toMatchObject(error)
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

    await expect(getThread('b', 42)).rejects.toMatchObject(error)
  })
})

describe('getThreadStatuses', () => {
  beforeEach(() => getMock.mockReset())

  it('returns the data on success', async () => {
    const statuses = [{ id: 1, board_slug: 'b', title: 'hello', is_locked: false, reply_count: 3, bump_at: '' }]
    getMock.mockResolvedValue({ data: statuses, error: undefined })

    await expect(getThreadStatuses([1, 2])).resolves.toBe(statuses)
    expect(getMock).toHaveBeenCalledWith('/api/threads/status', {
      params: { query: { ids: [1, 2] } },
    })
  })

  it('throws when the client returns an error', async () => {
    const error = { detail: 'too many ids' }
    getMock.mockResolvedValue({ data: undefined, error })

    await expect(getThreadStatuses([1])).rejects.toMatchObject(error)
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

    await expect(createThread('b', {}, [], 'tok', 'wrong')).rejects.toMatchObject(error)
  })

  it('sends a bearer token and omits captcha headers for an admin post', async () => {
    const thread = { id: 1, board_id: 1, title: 'T', is_locked: false, is_sticky: false, reply_count: 0, bump_at: '', created_at: '', posts: [] }
    fetchMock.mockResolvedValue({ ok: true, json: () => Promise.resolve(thread) })

    const file = new File(['img'], 'photo.jpg', { type: 'image/jpeg' })
    await createThread('b', { title: 'T', body: 'Hi' }, [file], null, null, 'admin-jwt')

    const [, options] = fetchMock.mock.calls[0] as [string, RequestInit]
    const headers = options.headers as Record<string, string>
    expect(headers['Authorization']).toBe('Bearer admin-jwt')
    expect(headers['X-Captcha-Token']).toBeUndefined()
    expect(headers['X-Captcha-Answer']).toBeUndefined()
  })
})

describe('createReply', () => {
  const fetchMock = vi.fn()
  beforeEach(() => {
    fetchMock.mockReset()
    vi.stubGlobal('fetch', fetchMock)
  })

  it('posts multipart form data to the thread posts endpoint and returns the post', async () => {
    const post = { id: 7, post_number: 102, thread_id: 42, board_id: 1, name: 'Anon', tripcode: null, body: 'Hi', body_html: '<p>Hi</p>', sage: false, is_op: false, is_edited: false, edited_at: null, created_at: '', attachments: [] }
    fetchMock.mockResolvedValue({ ok: true, json: () => Promise.resolve(post) })

    const result = await createReply('b', 42, { name: 'Anon', body: 'Hi', sage: true }, [], 'tok', 'ans')

    expect(result).toBe(post)
    expect(fetchMock).toHaveBeenCalledOnce()

    const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toContain('/api/b/threads/42/posts')
    expect(options.method).toBe('POST')
    expect((options.headers as Record<string, string>)['X-Captcha-Token']).toBe('tok')
    expect((options.headers as Record<string, string>)['X-Captcha-Answer']).toBe('ans')
    expect(options.body).toBeInstanceOf(FormData)
  })

  it('throws the parsed error body when response is not ok', async () => {
    const error = { detail: 'thread is locked' }
    fetchMock.mockResolvedValue({ ok: false, json: () => Promise.resolve(error), statusText: 'Forbidden' })

    await expect(createReply('b', 42, {}, [], 'tok', 'wrong')).rejects.toMatchObject(error)
  })

  it('sends a bearer token and omits captcha headers for an admin post', async () => {
    const post = { id: 7, post_number: 102 }
    fetchMock.mockResolvedValue({ ok: true, json: () => Promise.resolve(post) })

    await createReply('b', 42, { body: 'Hi' }, [], null, null, 'admin-jwt')

    const [, options] = fetchMock.mock.calls[0] as [string, RequestInit]
    const headers = options.headers as Record<string, string>
    expect(headers['Authorization']).toBe('Bearer admin-jwt')
    expect(headers['X-Captcha-Token']).toBeUndefined()
    expect(headers['X-Captcha-Answer']).toBeUndefined()
  })
})

