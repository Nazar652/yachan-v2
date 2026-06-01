import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

// the mod jwt is the only client-only state in the app, so pinia enters here.
// it is persisted to localStorage so a refresh keeps the mod logged in.
const TOKEN_KEY = 'yachan_mod_token'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))
  const isAuthenticated = computed(() => token.value !== null)

  function login(newToken: string) {
    token.value = newToken
    localStorage.setItem(TOKEN_KEY, newToken)
  }

  function logout() {
    token.value = null
    localStorage.removeItem(TOKEN_KEY)
  }

  return { token, isAuthenticated, login, logout }
})
