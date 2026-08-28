import { afterEach, beforeEach, describe, expect, it } from "vitest";
import fetchMock from "fetch-mock";

import { GET } from "./health";
import { getBackendUrl } from "../global/utils";

const HEALTH_ENDPOINT = `${getBackendUrl()}/api/health/`;

describe("GET /health", () => {
  beforeEach(() => {
    fetchMock.mockGlobal();
  });

  afterEach(() => {
    fetchMock.unmockGlobal();
    fetchMock.removeRoutes();
    fetchMock.callHistory.clear();
  });

  it("returns 200 with all checks passing when backend is healthy", async () => {
    fetchMock.route(HEALTH_ENDPOINT, { status: 200, body: { status: "ok" } });

    const response = await GET({} as Parameters<typeof GET>[0]);
    const body = await response.json();

    expect(response.status).toBe(200);
    expect(body.status).toBe("ok");
    expect(body.checks.backend.status).toBe("ok");
    expect(body.timestamp).toBeDefined();
  });

  it("returns 503 when backend returns a non-2xx response", async () => {
    fetchMock.route(HEALTH_ENDPOINT, {
      status: 503,
      body: "Service Unavailable",
    });

    const response = await GET({} as Parameters<typeof GET>[0]);
    const body = await response.json();

    expect(response.status).toBe(503);
    expect(body.status).toBe("error");
    expect(body.checks.backend.status).toBe("error");
  });

  it("returns 503 with unreachable status on network failure", async () => {
    fetchMock.route(HEALTH_ENDPOINT, { throws: new Error("fetch failed") });

    const response = await GET({} as Parameters<typeof GET>[0]);
    const body = await response.json();

    expect(response.status).toBe(503);
    expect(body.status).toBe("error");
    expect(body.checks.backend.status).toBe("unreachable");
    expect(body.checks.backend.detail).toBe("fetch failed");
  });

  it("returns 503 with unreachable status on timeout", async () => {
    const abortError = new DOMException(
      "The operation was aborted.",
      "AbortError",
    );
    fetchMock.route(HEALTH_ENDPOINT, { throws: abortError });

    const response = await GET({} as Parameters<typeof GET>[0]);
    const body = await response.json();

    expect(response.status).toBe(503);
    expect(body.status).toBe("error");
    expect(body.checks.backend.status).toBe("unreachable");
  });

  it("calls the correct backend health endpoint", async () => {
    fetchMock.route(HEALTH_ENDPOINT, { status: 200, body: { status: "ok" } });

    await GET({} as Parameters<typeof GET>[0]);

    expect(
      fetchMock.callHistory.calls().filter((c) => c.url === HEALTH_ENDPOINT),
    ).toHaveLength(1);
  });
});
