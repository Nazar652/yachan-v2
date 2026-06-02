import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import type { ModRole } from '@/api/types'

// the mod jwt + role are the only client-only state in the app, so pinia enters
// here. both are persisted to localStorage so a refresh keeps the mod logged in.
// the role only gates UI — every action is still authorized server-side.
const TOKEN_KEY = 'yachan_mod_token'
const ROLE_KEY = 'yachan_mod_role'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))
  const role = ref<ModRole | null>(localStorage.getItem(ROLE_KEY) as ModRole | null)

  const isAuthenticated = computed(() => token.value !== null)
  const isAdmin = computed(() => role.value === 'admin')

  function login(newToken: string, newRole: ModRole) {
    token.value = newToken
    role.value = newRole
    localStorage.setItem(TOKEN_KEY, newToken)
    localStorage.setItem(ROLE_KEY, newRole)
  }

  function logout() {
    token.value = null
    role.value = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(ROLE_KEY)
  }

  return { token, role, isAuthenticated, isAdmin, login, logout }
})
