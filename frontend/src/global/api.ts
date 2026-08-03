import type { APIContext, AstroGlobal } from "astro";

import { getBackendUrl } from "./utils";

interface FetchBackendApiReturn<T> {
  data?: T,
  status: number,
  error?: string,
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
      const error = await response.json();
      return ({
        status: response.status,
        error: error,
      });
    }

    if (response.status == 204) {
      // 204 No Content
      return ({
        status: 204,
        data: {} as T,
      });
    } else {
      return {
        status: response.status,
        data: await response.json() as T,
      };
    }
  } catch(err) {
    return ({
      status: 500,
      error: "Fetch failed - unknown error",
    })
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

export async function checkUrlStatus(
  astro: Readonly<AstroGlobal> | APIContext,
  url: string,
) {
  try {
    const { status } = await fetchBackendApi(astro, url);
    return status;
  } catch (err) {
    return (err as { status: number }).status || 500;
  }
}
