import { describe, expect, it } from 'vitest'

import { ApiError, errorDetail, toApiError } from '@/api/errors'

describe('toApiError', () => {
  it('wraps a fastapi { detail } body into an ApiError carrying status and detail', () => {
    const error = toApiError({ detail: 'not allowed' }, 403)

    expect(error).toBeInstanceOf(ApiError)
    expect(error).toBeInstanceOf(Error)
    expect(error.status).toBe(403)
    expect(error.detail).toBe('not allowed')
    expect(error.message).toBe('not allowed')
    expect(error.body).toEqual({ detail: 'not allowed' })
  })

  it('joins validation-error detail arrays into one message', () => {
    const error = toApiError({ detail: [{ msg: 'field required' }, { msg: 'too long' }] }, 422)

    expect(error.detail).toBe('field required; too long')
  })

  it('falls back to a status message when detail is empty or missing', () => {
    const error = toApiError({ detail: '' }, 500)

    expect(error.detail).toBeNull()
    expect(error.message).toBe('Request failed with status 500')
  })

  it('treats a plain string error as the detail', () => {
    const error = toApiError('boom')

    expect(error.detail).toBe('boom')
  })

  it('returns the same instance when given an ApiError', () => {
    const original = new ApiError('already wrapped', 404)

    expect(toApiError(original)).toBe(original)
  })
})

describe('errorDetail', () => {
  it('returns the ApiError detail when present', () => {
    expect(errorDetail(new ApiError('thread is locked', 403), 'fallback')).toBe('thread is locked')
  })

  it('returns the fallback for an ApiError without detail', () => {
    expect(errorDetail(new ApiError(null, 500), 'fallback')).toBe('fallback')
  })

  it('returns the fallback for a non-ApiError value', () => {
    expect(errorDetail(new Error('raw'), 'fallback')).toBe('fallback')
  })
})
