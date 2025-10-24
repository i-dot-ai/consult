export const prerender = false;

import { join } from "path";

import type { APIRoute } from "astro";

import { getBackendUrl } from "../../../global/utils";
import { Routes } from "../../../global/routes";

export const POST: APIRoute = async ({ request }) => {
  let message = "success";
  let status = 200;

  const requestBody = await request.json();

  try {
    const backendResponse = await fetch(
      join(getBackendUrl(request.url), Routes.ApiMagicLink),
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
  } catch (err: unknown) {
    if (err instanceof Error) {
      message = err.message;
    }
    message = "unknown";
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
