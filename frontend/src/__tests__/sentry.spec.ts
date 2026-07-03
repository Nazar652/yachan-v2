import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

const { initMock, browserTracingMock } = vi.hoisted(() => ({
  initMock: vi.fn(),
  browserTracingMock: vi.fn(() => ({ name: 'BrowserTracing' })),
}))

vi.mock('@sentry/vue', () => ({
  init: initMock,
  browserTracingIntegration: browserTracingMock,
}))

import { initSentry, isThirdPartyError } from '@/sentry'
import type { App } from 'vue'
import type { Router } from 'vue-router'

const app = {} as App
const router = {} as Router

function eventWithFrames(...filenames: (string | undefined)[]): Parameters<typeof isThirdPartyError>[0] {
  return {
    exception: { values: [{ stacktrace: { frames: filenames.map((filename) => ({ filename })) } }] },
  } as unknown as Parameters<typeof isThirdPartyError>[0]
}

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

  it('drops third-party errors via beforeSend, keeps our own', () => {
    vi.stubEnv('VITE_SENTRY_DSN', 'https://public@sentry.example/1')
    initSentry(app, router)

    const beforeSend = initMock.mock.calls[0]?.[0]?.beforeSend as (
      event: Parameters<typeof isThirdPartyError>[0],
    ) => unknown
    const ownEvent = eventWithFrames(`${window.location.origin}/assets/index.js`)
    const noiseEvent = eventWithFrames(`${window.location.origin}/assets/index.js`, '<anonymous>')

    expect(beforeSend(ownEvent)).toBe(ownEvent)
    expect(beforeSend(noiseEvent)).toBeNull()
  })
})

describe('isThirdPartyError', () => {
  const own = `${window.location.origin}/assets/index.js`

  it('keeps errors whose crash frame is our own bundle', () => {
    expect(isThirdPartyError(eventWithFrames(own, own))).toBe(false)
  })

  it('drops errors thrown from an injected anonymous script', () => {
    expect(isThirdPartyError(eventWithFrames(own, '<anonymous>'))).toBe(true)
  })

  it('drops errors thrown from a browser extension', () => {
    expect(isThirdPartyError(eventWithFrames('chrome-extension://abc/inject.js'))).toBe(true)
  })

  it('drops errors whose crash frame has no filename', () => {
    expect(isThirdPartyError(eventWithFrames(own, undefined))).toBe(true)
  })

  it('keeps events without a stacktrace (cannot attribute)', () => {
    expect(isThirdPartyError({} as Parameters<typeof isThirdPartyError>[0])).toBe(false)
  })
})
