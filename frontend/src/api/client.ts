import createClient, { type Middleware } from 'openapi-fetch'

import type { paths } from '@/api/schema'
import { useAuthStore } from '@/stores/auth'

// the single typed http client; paths/params/bodies/responses are all checked
// against the backend openapi schema.
export const apiClient = createClient<paths>({
  baseUrl: import.meta.env.VITE_API_BASE_URL,
})

// inject the mod bearer token (when logged in) on every request. the store is
// resolved lazily inside the callback so pinia is already active by request time.
export const authMiddleware: Middleware = {
  onRequest({ request }) {
    const { token } = useAuthStore()
    if (token) request.headers.set('Authorization', `Bearer ${token}`)
    return request
  },
}

apiClient.use(authMiddleware)
