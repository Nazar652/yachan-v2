import { describe, expect, it, vi, beforeEach } from 'vitest'
import { apiClient } from '@/api/client'
import { fetchCaptcha } from '@/api/captcha'

vi.mock('@/api/client', () => ({
  apiClient: { GET: vi.fn() },
}))

const getMock = vi.mocked(apiClient.GET)

describe('fetchCaptcha', () => {
  beforeEach(() => getMock.mockReset())

  it('returns captcha data on success', async () => {
    const captcha = { token: 'tok123', image_base64_light: 'abc==', image_base64_dark: 'def==' }
    getMock.mockResolvedValue({ data: captcha, error: undefined })

    await expect(fetchCaptcha()).resolves.toBe(captcha)
    expect(getMock).toHaveBeenCalledWith('/api/captcha')
  })

  it('throws when the client returns an error', async () => {
    const error = { detail: 'server error' }
    getMock.mockResolvedValue({ data: undefined, error })

    await expect(fetchCaptcha()).rejects.toMatchObject(error)
  })
})

