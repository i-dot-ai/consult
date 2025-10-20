import type { APIContext } from "astro";
import path from "path";

import { getBackendUrl } from "./utils";

export const fetchBackendApi = async <T>(
  Astro: APIContext,
  endpoint: string,
  options: RequestInit | undefined = {},
): Promise<T> => {
  const url = path.join(getBackendUrl(), endpoint);
  const accessToken = Astro.cookies.get("access")?.value;

  const response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      contentType: "application/json",
      Authorization: `Bearer ${accessToken}`,
      cookie: Astro.request.headers.get("cookie") || "",
    },
  });

  if (!response.ok) {
    let errorBody;
    try {
      errorBody = await response.json();
    } catch {
      errorBody = await response.text();
    }
    throw { status: response.status, error: errorBody };
  }

  return response.json() as Promise<T>;
};
