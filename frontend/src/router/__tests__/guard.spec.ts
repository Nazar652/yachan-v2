import { describe, expect, it, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import type { RouteLocationNormalized } from 'vue-router'

import { authGuard } from '@/router'
import { useAuthStore } from '@/stores/auth'

beforeEach(() => {
  localStorage.clear()
  setActivePinia(createPinia())
})

function route(meta: Record<string, unknown>): RouteLocationNormalized {
  return { meta } as RouteLocationNormalized
}

describe('authGuard', () => {
  it('redirects to the login page for a protected route when unauthenticated', () => {
    expect(authGuard(route({ requiresAuth: true }))).toEqual({ name: 'mod-login' })
  })

  it('allows a protected route when authenticated', () => {
    useAuthStore().login('jwt', 'admin')
    expect(authGuard(route({ requiresAuth: true }))).toBe(true)
  })

  it('allows a public route', () => {
    expect(authGuard(route({}))).toBe(true)
  })
})
