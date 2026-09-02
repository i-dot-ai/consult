import type { APIContext, MiddlewareHandler, MiddlewareNext } from "astro";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { LoggerAdapter } from "./logging";

const infoSpy = vi.fn();
const configureOtelMock = vi.fn(async () => undefined);
const createLoggerMock = vi.fn(() => ({ info: infoSpy }));

vi.mock("@i-dot-ai-npm/utilities-observability", () => ({
  configureOtel: configureOtelMock,
  createLogger: createLoggerMock,
}));

const loadLogger = async (): Promise<LoggerAdapter> => {
  vi.resetModules();
  return (await import("./logging")).default;
};

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
  beforeEach(() => {
    vi.clearAllMocks();
    configureOtelMock.mockResolvedValue(undefined);
    createLoggerMock.mockReturnValue({ info: infoSpy });
    process.env.OTEL_ENABLED = "true";
    process.env.OTEL_EXPORTER_OTLP_ENDPOINT = "http://collector:4318";
    process.env.OTEL_SERVICE_NAME = "consult-frontend";
  });

  afterEach(() => {
    delete process.env.OTEL_ENABLED;
    delete process.env.OTEL_EXPORTER_OTLP_ENDPOINT;
    delete process.env.OTEL_SERVICE_NAME;
  });

  it("stays a pass-through no-op unless OTel is fully configured", async () => {
    delete process.env.OTEL_ENABLED;

    const logger = await loadLogger();
    const { response, next } = await runMiddleware(logger);

    expect(configureOtelMock).not.toHaveBeenCalled();
    expect(createLoggerMock).not.toHaveBeenCalled();
    expect(infoSpy).not.toHaveBeenCalled();
    expect(next).toHaveBeenCalledOnce();
    expect(response.status).toBe(200);
  });

  it("logs each request with structured fields and passes through", async () => {
    const logger = await loadLogger();

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

  it("falls back to a pass-through no-op when OTel setup fails", async () => {
    configureOtelMock.mockRejectedValueOnce(new Error("otel unavailable"));
    const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});

    const logger = await loadLogger();
    const { response, next } = await runMiddleware(logger);

    expect(next).toHaveBeenCalledOnce();
    expect(response.status).toBe(200);
    expect(infoSpy).not.toHaveBeenCalled();
    expect(warnSpy).toHaveBeenCalledOnce();

    warnSpy.mockRestore();
  });
});
