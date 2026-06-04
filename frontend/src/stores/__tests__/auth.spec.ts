import { describe, expect, it, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

import { useAuthStore } from '@/stores/auth'

beforeEach(() => {
  localStorage.clear()
  setActivePinia(createPinia())
})

describe('useAuthStore', () => {
  it('starts unauthenticated when nothing is stored', () => {
    const auth = useAuthStore()
    expect(auth.token).toBeNull()
    expect(auth.role).toBeNull()
    expect(auth.isAuthenticated).toBe(false)
    expect(auth.isAdmin).toBe(false)
  })

  it('login stores the token and role, and marks an admin authenticated', () => {
    const auth = useAuthStore()
    auth.login('jwt-123', 'admin')
    expect(auth.token).toBe('jwt-123')
    expect(auth.role).toBe('admin')
    expect(auth.isAuthenticated).toBe(true)
    expect(auth.isAdmin).toBe(true)
    expect(localStorage.getItem('yachan_mod_token')).toBe('jwt-123')
    expect(localStorage.getItem('yachan_mod_role')).toBe('admin')
  })

  it('isAdmin is false for a moderator', () => {
    const auth = useAuthStore()
    auth.login('jwt-123', 'moderator')
    expect(auth.isAuthenticated).toBe(true)
    expect(auth.isAdmin).toBe(false)
  })

  it('logout clears the token, role and storage', () => {
    const auth = useAuthStore()
    auth.login('jwt-123', 'admin')
    auth.logout()
    expect(auth.token).toBeNull()
    expect(auth.role).toBeNull()
    expect(auth.isAuthenticated).toBe(false)
    expect(auth.isAdmin).toBe(false)
    expect(localStorage.getItem('yachan_mod_token')).toBeNull()
    expect(localStorage.getItem('yachan_mod_role')).toBeNull()
  })

  it('initializes the token and role from localStorage', () => {
    localStorage.setItem('yachan_mod_token', 'persisted')
    localStorage.setItem('yachan_mod_role', 'admin')
    const auth = useAuthStore()
    expect(auth.token).toBe('persisted')
    expect(auth.role).toBe('admin')
    expect(auth.isAuthenticated).toBe(true)
    expect(auth.isAdmin).toBe(true)
  })
})
