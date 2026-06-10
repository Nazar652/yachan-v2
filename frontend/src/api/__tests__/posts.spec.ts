import { describe, expect, it, vi, beforeEach } from 'vitest'

import { apiClient } from '@/api/client'
import { editPost, getPostHistory } from '@/api/posts'

vi.mock('@/api/client', () => ({
  apiClient: { GET: vi.fn(), PATCH: vi.fn() },
}))

const getMock = vi.mocked(apiClient.GET)
const patchMock = vi.mocked(apiClient.PATCH)

describe('editPost', () => {
  beforeEach(() => patchMock.mockReset())

  it('patches the post and returns the data on success', async () => {
    const post = { id: 1, post_number: 7, is_edited: true }
    patchMock.mockResolvedValue({ data: post, error: undefined } as never)

    await expect(editPost('b', 7, 'new text')).resolves.toBe(post)
    expect(patchMock).toHaveBeenCalledWith('/api/{board_slug}/posts/{post_number}', {
      params: { path: { board_slug: 'b', post_number: 7 } },
      body: { new_body: 'new text' },
    })
  })

  it('throws when the client returns an error', async () => {
    const error = { detail: 'boom' }
    patchMock.mockResolvedValue({ data: undefined, error } as never)

    await expect(editPost('b', 7, 'x')).rejects.toBe(error)
  })
})

describe('getPostHistory', () => {
  beforeEach(() => getMock.mockReset())

  it('returns the edit on success', async () => {
    const edit = { post_id: 1, original_body: 'old', original_body_html: '<p>old</p>' }
    getMock.mockResolvedValue({ data: edit, error: undefined } as never)

    await expect(getPostHistory('b', 7)).resolves.toBe(edit)
    expect(getMock).toHaveBeenCalledWith('/api/{board_slug}/posts/{post_number}/history', {
      params: { path: { board_slug: 'b', post_number: 7 } },
    })
  })

  it('returns null when the post was never edited', async () => {
    getMock.mockResolvedValue({ data: null, error: undefined } as never)

    await expect(getPostHistory('b', 7)).resolves.toBeNull()
  })

  it('throws when the client returns an error', async () => {
    const error = { detail: 'boom' }
    getMock.mockResolvedValue({ data: undefined, error } as never)

    await expect(getPostHistory('b', 7)).rejects.toBe(error)
  })
})
