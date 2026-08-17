import { describe, expect, it } from "vitest";

import type { ErrorEvent } from "@sentry/astro";

import { getTracesSampleRate, sanitizeSentryEvent } from "./sentry";

describe("sanitizeSentryEvent", () => {
  it("strips sensitive headers case-insensitively", () => {
    const event = {
      request: {
        headers: {
          "X-Amzn-Oidc-Data": "signed-token",
          Authorization: "Bearer abc",
          Cookie: "session=123",
          "Content-Type": "application/json",
        },
      },
    } as unknown as ErrorEvent;

    const result = sanitizeSentryEvent(event);

    expect(result.request?.headers).toEqual({
      "Content-Type": "application/json",
    });
  });

  it("does not mutate the original headers object", () => {
    const headers = {
      Authorization: "Bearer abc",
      "Content-Type": "application/json",
    };
    const event = { request: { headers } } as unknown as ErrorEvent;

    sanitizeSentryEvent(event);

    expect(headers).toEqual({
      Authorization: "Bearer abc",
      "Content-Type": "application/json",
    });
  });

  it("deletes request cookies", () => {
    const event = {
      request: {
        headers: {},
        cookies: { session: "123" },
      },
    } as unknown as ErrorEvent;

    const result = sanitizeSentryEvent(event);

    expect(result.request?.cookies).toBeUndefined();
  });

  it("no-ops when the event has no request", () => {
    const event = { message: "boom" } as ErrorEvent;

    expect(() => sanitizeSentryEvent(event)).not.toThrow();
    expect(sanitizeSentryEvent(event)).toBe(event);
  });
});

describe("getTracesSampleRate", () => {
  it("samples at a low rate in deployed prod-like envs", () => {
    expect(getTracesSampleRate("prod")).toEqual(0.1);
    expect(getTracesSampleRate("preprod")).toEqual(0.1);
  });

  it("samples everything in developer-facing envs", () => {
    expect(getTracesSampleRate("dev")).toEqual(1.0);
    expect(getTracesSampleRate("local")).toEqual(1.0);
  });

  it("matches case-insensitively", () => {
    expect(getTracesSampleRate("PROD")).toEqual(0.1);
    expect(getTracesSampleRate("Local")).toEqual(1.0);
  });

  it("stays low for an unknown or missing env", () => {
    expect(getTracesSampleRate(undefined)).toEqual(0.1);
    expect(getTracesSampleRate("")).toEqual(0.1);
  });
});
