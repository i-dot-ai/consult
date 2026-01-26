import type { APIContext, AstroGlobal } from "astro";
import path from "path";

import { getBackendUrl } from "./utils";

export const internalAccessCookieName = "gdsInternalAccess";

export const fetchBackendApi = async <T>(
  astro: Readonly<AstroGlobal> | APIContext,
  endpoint: string,
  options: RequestInit | undefined = {},
): Promise<T> => {
  const url = path.join(getBackendUrl(), endpoint);
  const accessToken = astro.cookies.get(internalAccessCookieName)?.value;
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
    throw { status: response.status, error };
  }

  if (response.status == 204) {
    // 204 No Content
    return {} as Promise<T>;
  } else {
    return response.json() as Promise<T>;
  }
};
