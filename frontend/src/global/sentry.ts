import type { ErrorEvent, EventHint } from "@sentry/astro";

// The ALB adds x-amzn-oidc-* identity headers to every request; these and the
// session cookie must never reach Sentry.
const SENSITIVE_HEADERS = new Set([
  "x-amzn-oidc-data",
  "x-amzn-oidc-accesstoken",
  "x-amzn-oidc-identity",
  "authorization",
  "cookie",
  "set-cookie",
  "x-api-key",
]);

export const sanitizeSentryEvent = (
  event: ErrorEvent,
  _hint?: EventHint,
): ErrorEvent => {
  const request = event.request;
  if (!request) {
    return event;
  }

  if (request.headers) {
    const headers = { ...request.headers };
    for (const key of Object.keys(headers)) {
      if (SENSITIVE_HEADERS.has(key.toLowerCase())) {
        delete headers[key];
      }
    }
    request.headers = headers;
  }

  delete request.cookies;

  return event;
};

export const getTracesSampleRate = (environment?: string): number => {
  const env = environment?.toLowerCase();
  return env === "local" || env === "dev" ? 1.0 : 0.1;
};
