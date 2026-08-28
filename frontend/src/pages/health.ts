import type { APIRoute } from "astro";
import { getBackendUrl } from "../global/utils";

type BackendHealthStatus = "ok" | "error" | "unreachable";

interface HealthResponse {
  status: "ok" | "error";
  timestamp: string;
  checks: {
    backend: {
      status: BackendHealthStatus;
      detail?: unknown;
    };
  };
}

export const GET: APIRoute = async () => {
  const timestamp = new Date().toISOString();
  let backendStatus: BackendHealthStatus = "unreachable";
  let backendDetail: unknown = undefined;

  try {
    const backendUrl = getBackendUrl();
    const response = await fetch(
      new URL("/api/health/", backendUrl).toString(),
      {
        signal: AbortSignal.timeout(5000),
      },
    );

    if (response.ok) {
      backendStatus = "ok";
    } else {
      backendStatus = "error";
      backendDetail = await response.text();
    }
  } catch (err) {
    if (err instanceof Error) {
      backendDetail = err.message;
    }
  }

  const overall = backendStatus === "ok" ? "ok" : "error";
  const httpStatus = overall === "ok" ? 200 : 503;

  const body: HealthResponse = {
    status: overall,
    timestamp,
    checks: {
      backend: {
        status: backendStatus,
        ...(backendDetail !== undefined ? { detail: backendDetail } : {}),
      },
    },
  };

  return new Response(JSON.stringify(body), {
    status: httpStatus,
    headers: {
      "Content-Type": "application/json",
    },
  });
};
