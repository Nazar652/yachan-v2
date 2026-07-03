import * as Sentry from '@sentry/vue'
import type { App } from 'vue'
import type { Router } from 'vue-router'

// our global handlers also catch errors thrown by browser extensions, injected
// webview bridges and other third-party scripts. keep only errors whose crash
// site (the newest frame) is served from our own origin; drop the rest.
export function isThirdPartyError(event: Sentry.ErrorEvent): boolean {
  const frames = event.exception?.values?.flatMap((value) => value.stacktrace?.frames ?? []) ?? []
  if (frames.length === 0) return false
  const crashFrame = frames[frames.length - 1]
  return !crashFrame?.filename || !crashFrame.filename.startsWith(window.location.origin)
}

export function initSentry(app: App, router: Router): void {
  const dsn = import.meta.env.VITE_SENTRY_DSN
  if (!dsn) return
  Sentry.init({
    app,
    dsn,
    environment: import.meta.env.VITE_SENTRY_ENVIRONMENT,
    integrations: [Sentry.browserTracingIntegration({ router })],
    tracesSampleRate: 1.0,
    beforeSend: (event) => (isThirdPartyError(event) ? null : event),
  })
}
