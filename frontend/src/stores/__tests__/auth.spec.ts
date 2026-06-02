import { describe, expect, it, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

import { useAuthStore } from '@/stores/auth'

beforeEach(() => {
  localStorage.clear()
  setActivePinia(createPinia())
})

describe('useAuthStore', () => {
  it('starts unauthenticated when no token is stored', () => {
    const auth = useAuthStore()
    expect(auth.token).toBeNull()
    expect(auth.isAuthenticated).toBe(false)
  })

  it('login stores the token and marks the user authenticated', () => {
    const auth = useAuthStore()
    auth.login('jwt-123')
    expect(auth.token).toBe('jwt-123')
    expect(auth.isAuthenticated).toBe(true)
    expect(localStorage.getItem('yachan_mod_token')).toBe('jwt-123')
  })

  it('logout clears the token and storage', () => {
    const auth = useAuthStore()
    auth.login('jwt-123')
    auth.logout()
    expect(auth.token).toBeNull()
    expect(auth.isAuthenticated).toBe(false)
    expect(localStorage.getItem('yachan_mod_token')).toBeNull()
  })

  it('initializes the token from localStorage', () => {
    localStorage.setItem('yachan_mod_token', 'persisted')
    const auth = useAuthStore()
    expect(auth.token).toBe('persisted')
    expect(auth.isAuthenticated).toBe(true)
  })
})
