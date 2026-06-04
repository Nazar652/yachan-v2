import { describe, expect, it, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import type { Middleware } from 'openapi-fetch'

import { authMiddleware } from '@/api/client'
import { useAuthStore } from '@/stores/auth'

type OnRequestArg = Parameters<NonNullable<Middleware['onRequest']>>[0]

beforeEach(() => {
  localStorage.clear()
  setActivePinia(createPinia())
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
})
