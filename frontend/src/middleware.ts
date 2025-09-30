import path from "path";

import type { MiddlewareHandler } from "astro";
import { getBackendUrl } from "./global/utils";

export const onRequest: MiddlewareHandler = async (context, next) => {
  const accessToken = context.cookies.get("access")?.value;
  const url = context.url;

  // Redirect to sign-in if not logged in
  const protectedRoutes = [
    // /^\/sign-out[\/]?$/,
    /^\/consultations.*/,
    /^\/design.*/,
  ];

  for (const protectedRoute of protectedRoutes) {
    if (
      protectedRoute.test(url.pathname) &&
      !context.cookies.get("access")?.value
    ) {
      return context.redirect("/sign-in");
    }
  }

  const backendUrl = getBackendUrl(url.hostname);
  const fullBackendUrl = path.join(backendUrl, url.pathname) + url.search;

  // skip as new pages are moved to astro
  const toSkip = [
    /^\/$/,
    /^\/data-sharing[/]?$/,
    /^\/get-involved[/]?$/,
    /^\/how-it-works[/]?$/,
    /^\/privacy[/]?$/,
    /^\/sign-in[/]?$/,
    /^\/sign-out[/]?$/,
    /^\/magic-link\/[A-Za-z0-9-]*[/]?$/,
    /^\/api\/astro\/.*/,
    /^\/api\/health[/]?$/,
    /^\/health[/]?$/,
    /^\/.well-known\/.*/,
    /^\/consultations.*/,
    // /^\/evaluations.*/,
    /^\/design.*/,
    /^\/_astro.*/,
  ];

  for (const skipPattern of toSkip) {
    if (skipPattern.test(context.url.pathname)) {
      return next();
    }
  }

  const hasBody = !["GET", "HEAD"].includes(context.request.method);
  const csrfCookie = context.cookies.get("csrftoken");

  try {
    // Get all cookies and forward them
    const cookieHeader = context.request.headers.get("cookie") || "";

    // Handle request body properly for forms
    let requestBody = undefined;
    if (hasBody) {
      try {
        requestBody = await context.request.arrayBuffer();
        console.log("Request body size:", requestBody?.byteLength || 0);
        if (requestBody && requestBody.byteLength > 0) {
          // Convert to string to see what we're sending (for debugging)
          const bodyText = new TextDecoder().decode(requestBody);
          console.log("Request body content:", bodyText.substring(0, 200)); // First 200 chars
        }
      } catch (e) {
        console.error("Error reading request body:", e);
      }
    }

    // Create headers object properly
    const headersToSend = new Headers();

    // Copy all original headers
    for (const [key, value] of context.request.headers.entries()) {
      headersToSend.set(key, value);
    }

    // Add/override specific headers
    headersToSend.set("Authorization", `Bearer ${accessToken}`);
    headersToSend.set("Cookie", cookieHeader);
    if (csrfCookie) {
      headersToSend.set("X-CSRFToken", csrfCookie.value);
    }

    if (hasBody) {
      console.log(
        "Content-Type header:",
        context.request.headers.get("content-type"),
      );
      console.log(
        "All headers being sent:",
        Object.fromEntries(headersToSend.entries()),
      );
    }

    const response = await fetch(fullBackendUrl, {
      method: context.request.method,
      headers: headersToSend,
      body: requestBody,
      redirect: "manual",
    });

    if (response.status === 401) {
      return context.redirect("/sign-out");
    }

    if (response.status === 304) {
      return response;
    }

    const redirectStatuses = [301, 302, 303, 307, 308] as const;
    type RedirectStatus = (typeof redirectStatuses)[number];
    if (redirectStatuses.includes(response.status as RedirectStatus)) {
      const location = response.headers.get("location");
      if (location) {
        return context.redirect(location, response.status as RedirectStatus);
      }
    }

    const body = await response.arrayBuffer();

    // Create new response and forward all headers including Set-Cookie
    const newResponse = new Response(body, {
      status: response.status,
      headers: response.headers,
    });

    return newResponse;
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "unknown";
    console.log("Error 500:", message);
    return new Response(JSON.stringify({ message }), {
      status: 500,
    });
  }
};
