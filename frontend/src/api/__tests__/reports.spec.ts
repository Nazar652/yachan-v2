import { describe, expect, it, vi, beforeEach } from 'vitest'

import { apiClient } from '@/api/client'
import { createReport } from '@/api/reports'

vi.mock('@/api/client', () => ({
  apiClient: { POST: vi.fn() },
}))

const postMock = vi.mocked(apiClient.POST)

describe('createReport', () => {
  beforeEach(() => postMock.mockReset())

  it('posts the reason to the report endpoint', async () => {
    postMock.mockResolvedValue({ error: undefined } as never)

    await expect(createReport('b', 101, 'spam')).resolves.toBeUndefined()
    expect(postMock).toHaveBeenCalledWith('/api/{board_slug}/posts/{post_number}/report', {
      params: { path: { board_slug: 'b', post_number: 101 } },
      body: { reason: 'spam' },
    })
  })

  it('passes a null reason through unchanged', async () => {
    postMock.mockResolvedValue({ error: undefined } as never)

    await createReport('b', 101, null)
    expect(postMock).toHaveBeenCalledWith('/api/{board_slug}/posts/{post_number}/report', {
      params: { path: { board_slug: 'b', post_number: 101 } },
      body: { reason: null },
    })
  })

  it('throws an ApiError when the client returns an error', async () => {
    postMock.mockResolvedValue({
      error: { detail: 'too many reports, slow down' },
      response: new Response(null, { status: 429 }),
    } as never)

    await expect(createReport('b', 101, null)).rejects.toMatchObject({
      status: 429,
      detail: 'too many reports, slow down',
    })
  })
})
