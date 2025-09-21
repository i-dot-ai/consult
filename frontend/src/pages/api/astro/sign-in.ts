export const prerender = false;

import type { APIRoute } from "astro";

import { getBackendUrl } from "../../../global/utils";

export const POST: APIRoute = async ({ request }) => {
  let message = "success";
  let status = 200;

  const requestBody = await request.json();

  try {
    const backendResponse = await fetch(
      `${getBackendUrl(request.url)}/api/magic-link/`,
      {
        method: "POST",
        body: JSON.stringify({
          email: requestBody.email,
        }),
        headers: {
          "Content-Type": "application/json",
        },
      },
    );
    if (!backendResponse.ok) {
      message = "Response not ok";
      status = 500;
    }
  } catch (err: any) {
    message = err?.message || "unknown";
    status = 500;
  }

  return new Response(
    JSON.stringify({
      message: message,
    }),
    {
      status: status,
    },
  );
};
