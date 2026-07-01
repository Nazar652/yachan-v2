import { describe, expect, it, beforeEach, afterEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import type { Middleware } from 'openapi-fetch'

import { authMiddleware } from '@/api/client'
import { useAuthStore } from '@/stores/auth'

type OnRequestArg = Parameters<NonNullable<Middleware['onRequest']>>[0]
type OnResponseArg = Parameters<NonNullable<Middleware['onResponse']>>[0]

const originalLocation = window.location

beforeEach(() => {
  localStorage.clear()
  setActivePinia(createPinia())
  Object.defineProperty(window, 'location', {
    configurable: true,
    value: { ...originalLocation, href: '' },
  })
})

afterEach(() => {
  Object.defineProperty(window, 'location', { configurable: true, value: originalLocation })
})

// a minimal request whose headers behave like the real Headers (set/get),
// so the middleware can be exercised without depending on global Request.
function fakeRequest() {
  const store = new Map<string, string>()
  return {
    headers: {
      set: (key: string, value: string) => store.set(key.toLowerCase(), value),
      get: (key: string) => store.get(key.toLowerCase()) ?? null,
    },
  }
}

function runOnRequest(request: ReturnType<typeof fakeRequest>) {
  authMiddleware.onRequest?.({ request } as unknown as OnRequestArg)
}

function runOnResponse(status: number) {
  return authMiddleware.onResponse?.({ response: { status } } as unknown as OnResponseArg)
}

describe('authMiddleware', () => {
  it('adds a bearer authorization header when a token is present', () => {
    useAuthStore().login('jwt-xyz', 'admin')
    const request = fakeRequest()
    runOnRequest(request)
    expect(request.headers.get('Authorization')).toBe('Bearer jwt-xyz')
  })

  it('leaves the request untouched when there is no token', () => {
    const request = fakeRequest()
    runOnRequest(request)
    expect(request.headers.get('Authorization')).toBeNull()
  })

  it('logs out and redirects to mod login on a 401 while a session was active', () => {
    useAuthStore().login('jwt-xyz', 'admin')
    runOnResponse(401)
    expect(useAuthStore().token).toBeNull()
    expect(window.location.href).toBe('/mod/login?sessionExpired=1')
  })

  it('does not log out or redirect on a 401 with no active session (e.g. a failed login)', () => {
    runOnResponse(401)
    expect(window.location.href).toBe('')
  })

  it('leaves the session untouched on a non-401 response', () => {
    useAuthStore().login('jwt-xyz', 'admin')
    runOnResponse(200)
    expect(useAuthStore().token).toBe('jwt-xyz')
    expect(window.location.href).toBe('')
  })
})
