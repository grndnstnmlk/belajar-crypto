/**
 * Sentry Frontend Telemetry & Performance Monitoring
 * Automatically captures unhandled exceptions, network errors,
 * and component crash boundaries.
 */

import * as Sentry from "@sentry/react";

export function initFrontendSentry() {
  const dsn = (import.meta as any).env?.VITE_SENTRY_DSN || "";
  const environment = (import.meta as any).env?.VITE_SENTRY_ENVIRONMENT || "production";

  if (!dsn) {
    // Sentry ready in offline/local mock mode
    return;
  }

  Sentry.init({
    dsn,
    environment,
    integrations: [
      Sentry.browserTracingIntegration(),
      Sentry.replayIntegration()
    ],
    tracesSampleRate: 1.0,
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1.0,
    beforeSend(event) {
      // Client-side credential scrubber
      if (event.request?.headers) {
        delete event.request.headers["authorization"];
        delete event.request.headers["x-mbx-apikey"];
      }
      return event;
    }
  });
}

export { Sentry };
