import type { APIContext, MiddlewareHandler, MiddlewareNext } from "astro";
import { beforeAll, describe, expect, it, vi } from "vitest";

import type { LoggerAdapter } from "./logging";

const infoSpy = vi.fn();

vi.mock("@i-dot-ai-npm/utilities-observability", () => ({
  configureOtel: vi.fn(async () => undefined),
  createLogger: vi.fn(() => ({ info: infoSpy })),
}));

const runMiddleware = async (
  logger: LoggerAdapter,
  {
    path = "/consultations",
    method = "GET",
    status = 200,
    contextId = "ctx-1",
  } = {},
) => {
  const request = new Request(`http://localhost:3000${path}`, { method });
  const next = vi.fn(
    async () => new Response(null, { status }),
  ) as unknown as MiddlewareNext;
  const context = { locals: { contextId }, request } as unknown as APIContext;
  const response = (await (logger.middleware as MiddlewareHandler)(
    context,
    next,
  )) as Response;
  return { response, next };
};

describe("logging middleware", () => {
  let logger: LoggerAdapter;

  // Env must be set before the module evaluates its top-level gate.
  beforeAll(async () => {
    process.env.OTEL_ENABLED = "true";
    process.env.OTEL_EXPORTER_OTLP_ENDPOINT = "http://collector:4318";
    logger = (await import("./logging")).default;
  });

  it("logs each request with structured fields and passes through", async () => {
    const { response, next } = await runMiddleware(logger, {
      path: "/consultations/42",
      method: "POST",
      status: 201,
      contextId: "ctx-abc",
    });

    expect(next).toHaveBeenCalledOnce();
    expect(response.status).toBe(201);
    expect(infoSpy).toHaveBeenCalledOnce();

    const [fields, message] = infoSpy.mock.calls[0];
    expect(message).toBe("request completed");
    expect(fields).toMatchObject({
      contextId: "ctx-abc",
      method: "POST",
      path: "/consultations/42",
      status: 201,
    });
    expect(fields.durationMs).toBeTypeOf("number");
  });
});
