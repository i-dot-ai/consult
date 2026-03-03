import type { APIRoute } from "astro";
import { getBackendUrl } from "../../global/utils";

const handler: APIRoute = async ({ params, request, cookies }) => {
  const backendUrl = getBackendUrl();
  const path = params.path || "";
  const url = new URL(request.url);
  const fullBackendUrl = new URL(
    `/api/${path}/${url.search}`,
    backendUrl,
  ).toString();

  const accessToken = cookies.get("accessToken")?.value;
  const cookieHeader = request.headers.get("cookie") || "";

  // Build headers to forward
  const headersToSend = new Headers();
  for (const [key, value] of request.headers.entries()) {
    // Skip host header as it will be set by fetch
    if (key.toLowerCase() !== "host") {
      headersToSend.set(key, value);
    }
  }

  // Set auth headers
  if (accessToken) {
    headersToSend.set("Authorization", `Bearer ${accessToken}`);
  }
  headersToSend.set("Cookie", cookieHeader);

  // Handle request body for non-GET/HEAD/DELETE requests
  const hasBody = !["GET", "HEAD", "DELETE"].includes(request.method);
  let requestBody: ArrayBuffer | undefined;
  if (hasBody) {
    try {
      requestBody = await request.arrayBuffer();
    } catch (e) {
      console.error("Error reading request body:", e);
      return new Response(
        JSON.stringify({ error: "Failed to read request body" }),
        {
          status: 400,
          headers: { "Content-Type": "application/json" },
        },
      );
    }
  }

  try {
    const response = await fetch(fullBackendUrl, {
      method: request.method,
      headers: headersToSend,
      body: requestBody,
      redirect: "follow",
    });

    // Return response as-is for 204/304
    if (response.status === 204 || response.status === 304) {
      return new Response(null, {
        status: response.status,
        headers: response.headers,
      });
    }

    const body = await response.arrayBuffer();

    return new Response(body, {
      status: response.status,
      headers: response.headers,
    });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Unknown error";
    console.error("API proxy error:", message);
    return new Response(JSON.stringify({ error: message }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
};

// Export handlers for all HTTP methods
export const GET = handler;
export const POST = handler;
export const PUT = handler;
export const PATCH = handler;
export const DELETE = handler;
export const OPTIONS = handler;
