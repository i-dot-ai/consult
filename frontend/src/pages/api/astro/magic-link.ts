export const prerender = false;

import type { APIRoute } from "astro";

import { getBackendUrl } from "../../../global/utils";

export const POST: APIRoute = async ({ request, cookies }) => {
  let status = 200;

  interface TokenData {
    access?: string;
    refresh?: string;
    sessionId?: string;
  }
  let data: TokenData = {};

  const requestBody = await request.json();

  try {
    const backendResponse = await fetch(`${getBackendUrl()}/api/token/`, {
      method: "POST",
      body: JSON.stringify({
        token: requestBody.token,
      }),
      headers: {
        "Content-Type": "application/json",
      },
    });

    const responseJson = await backendResponse.json();
    if (!backendResponse.ok) {
      status = 500;
    }
    data = responseJson;

    if (data.access) {
      cookies.set("access", data.access, { path: "/", sameSite: "lax" });
    }
    if (data.refresh) {
      cookies.set("refresh", data.refresh, { path: "/", sameSite: "lax" });
    }
    if (data.sessionId) {
      cookies.set("sessionId", data.sessionId, { path: "/", sameSite: "lax" });
    }
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
  } catch (err: unknown) {
    status = 500;
  }

  return new Response(JSON.stringify(data), {
    status: status,
  });
};
