import type { APIContext, AstroGlobal } from "astro";

import { getBackendUrl } from "./utils";

interface FetchBackendApiReturn<T> {
  data?: T;
  status: number;
  error?: unknown;
}
export const fetchBackendApi = async <T>(
  astro: Readonly<AstroGlobal> | APIContext,
  endpoint: string,
  options: RequestInit | undefined = {},
): Promise<FetchBackendApiReturn<T>> => {
  const url = new URL(endpoint, getBackendUrl()).toString();
  const accessToken = astro.cookies.get("accessToken")?.value;

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        ...options.headers,
        contentType: "application/json",
        Authorization: `Bearer ${accessToken}`,
        cookie: astro.request.headers.get("cookie") || "",
      },
    });

    if (!response.ok) {
      const error = response.headers
        .get("content-type")
        ?.includes("application/json")
        ? await response.json()
        : await response.text();

      return {
        status: response.status,
        error: error,
      };
    }

    if (response.status === 204) {
      // 204 No Content
      return {
        status: 204,
        data: {} as T,
      };
    } else {
      return {
        status: response.status,
        data: (await response.json()) as T,
      };
    }
  } catch (error) {
    if (error instanceof Error) {
      console.error(`${error.name}: ${error.message}`);
    } else {
      console.error(error);
    }

    return {
      status: 500,
      error: "Fetch failed - unknown error",
    };
  }
};

export function buildResponse(statusCode: number) {
  const STATUSES = {
    403: "Unauthorized",
    404: "Not Found",
    500: "Server Error",
  };
  return new Response(null, {
    status: statusCode,
    statusText: [403, 404, 500].includes(statusCode)
      ? STATUSES[statusCode as 403 | 404 | 500]
      : "Error",
  });
}
