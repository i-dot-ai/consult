import type { APIContext, AstroGlobal } from "astro";
import path from "path";

import { getBackendUrl, getEnv } from "./utils";

export const fetchBackendApi = async <T>(
  astro: Readonly<AstroGlobal> | APIContext,
  endpoint: string,
  options: RequestInit | undefined = {},
): Promise<T> => {
  const url = path.join(getBackendUrl(), endpoint);
  const env = getEnv().toLowerCase();

  let accessToken: string | null | undefined;
  if (env === "local" || env === "test" || env == null) {
    accessToken =
      process.env.TEST_INTERNAL_ACCESS_TOKEN ||
      import.meta.env?.TEST_INTERNAL_ACCESS_TOKEN;
  } else {
    accessToken = astro.request.headers.get("x-amzn-oidc-data");
  }

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
