// the api layer throws this instead of the raw openapi-fetch error body, so a
// failed request surfaces as a real Error (message + stack) rather than a bare
// object. that keeps catch blocks typed (status/detail) and stops sentry from
// reporting unserialisable "Object captured as exception" issues.
export class ApiError extends Error {
  readonly status: number
  readonly detail: string | null
  readonly body: unknown

  constructor(detail: string | null, status = 0, body?: unknown) {
    super(detail ?? `Request failed${status ? ` with status ${status}` : ''}`)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
    this.body = body
  }
}

// `source` accepts either an http status number or the fetch Response (whose
// `.status` is read); openapi-fetch types `response` as never for endpoints with
// no error schema, so the wrappers pass it as-is and let this resolve the status.
export function toApiError(error: unknown, source?: unknown): ApiError {
  if (error instanceof ApiError) return error
  return new ApiError(extractDetail(error), statusFrom(source), error)
}

function statusFrom(source: unknown): number {
  if (typeof source === 'number') return source
  if (source instanceof Response) return source.status
  return 0
}

// the user-facing message for a failed request: the api detail when present,
// otherwise the given fallback.
export function errorDetail(error: unknown, fallback: string): string {
  return error instanceof ApiError && error.detail ? error.detail : fallback
}

// fastapi error bodies are `{ detail: string }` or, on validation errors,
// `{ detail: [{ msg, ... }] }`; fall back to null when neither shape matches.
function extractDetail(error: unknown): string | null {
  if (typeof error === 'string') return error || null
  if (!error || typeof error !== 'object') return null
  const detail = (error as { detail?: unknown }).detail
  if (typeof detail === 'string') return detail || null
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => (item && typeof item === 'object' ? (item as { msg?: unknown }).msg : null))
      .filter((msg): msg is string => typeof msg === 'string')
    return messages.length ? messages.join('; ') : null
  }
  return null
}
