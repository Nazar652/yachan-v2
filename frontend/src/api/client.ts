import createClient from 'openapi-fetch'

import type { paths } from '@/api/schema'

// the single typed http client; paths/params/bodies/responses are all checked
// against the backend openapi schema. auth middleware is added in the mod step.
export const apiClient = createClient<paths>({
  baseUrl: import.meta.env.VITE_API_BASE_URL,
})
