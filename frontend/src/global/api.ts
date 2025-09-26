import type { APIContext } from "astro";
import { getBackendUrl } from "./utils";

export const fetchBackendApi = async <T>(
  Astro: APIContext,
  path: string,
  options: RequestInit = {},
): Promise<T> => {
  const url = `${getBackendUrl()}${path}`;
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
