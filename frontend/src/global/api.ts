import type { APIContext } from "astro";
import path from "path";

import { getBackendUrl } from "./utils";

export const fetchBackendApi = async <T>(
  Astro: APIContext,
  endpoint: string,
  options: RequestInit = {},
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
    const error = await response.json();
    throw { status: response.status, error };
  }

  return response.json() as Promise<T>;
};
