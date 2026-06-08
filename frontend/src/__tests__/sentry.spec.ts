import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

const { initMock, browserTracingMock } = vi.hoisted(() => ({
  initMock: vi.fn(),
  browserTracingMock: vi.fn(() => ({ name: 'BrowserTracing' })),
}))

vi.mock('@sentry/vue', () => ({
  init: initMock,
  browserTracingIntegration: browserTracingMock,
}))

import { initSentry } from '@/sentry'
import type { App } from 'vue'
import type { Router } from 'vue-router'

const app = {} as App
const router = {} as Router

beforeEach(() => {
  initMock.mockClear()
  browserTracingMock.mockClear()
})

afterEach(() => {
  vi.unstubAllEnvs()
})

describe('initSentry', () => {
  it('does nothing when no dsn is configured', () => {
    vi.stubEnv('VITE_SENTRY_DSN', '')
    initSentry(app, router)
    expect(initMock).not.toHaveBeenCalled()
  })

  it('initialises sentry with tracing when a dsn is configured', () => {
    vi.stubEnv('VITE_SENTRY_DSN', 'https://public@sentry.example/1')
    vi.stubEnv('VITE_SENTRY_ENVIRONMENT', 'production')

    initSentry(app, router)

    expect(initMock).toHaveBeenCalledExactlyOnceWith(expect.objectContaining({
        dsn: 'https://public@sentry.example/1',
        environment: 'production',
        tracesSampleRate: 1,
      }))
    expect(browserTracingMock).toHaveBeenCalledWith({ router })
  })
})
