import createClient, { type Middleware } from 'openapi-fetch'

import type { paths } from '@/api/schema'
import { useAuthStore } from '@/stores/auth'

export const apiClient = createClient<paths>({
  baseUrl: import.meta.env.VITE_API_BASE_URL,
})

// the store is resolved lazily inside the callbacks so pinia is already active by request time.
export const authMiddleware: Middleware = {
  onRequest({ request }) {
    const { token } = useAuthStore()
    if (token) request.headers.set('Authorization', `Bearer ${token}`)
    return request
  },
  onResponse({ response }) {
    if (response.status === 401) {
      const auth = useAuthStore()
      // only a stale/expired session forces a redirect - a 401 with no token
      // active is just a failed login attempt, handled by the caller. a hard
      // navigation (not router.push) keeps this module decoupled from the router.
      if (auth.token) {
        auth.logout()
        window.location.href = '/mod/login?sessionExpired=1'
      }
    }

    return response
  },
}

apiClient.use(authMiddleware)
