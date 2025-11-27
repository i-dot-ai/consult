import path from "path";

import type { MiddlewareHandler } from "astro";
import { Routes } from "./global/routes";
import { fetchBackendApi } from "./global/api";
import { getBackendUrl } from "./global/utils";

export const onRequest: MiddlewareHandler = async (context, next) => {
  let userIsStaff: boolean = false;

  const accessToken = context.cookies.get("access")?.value;
  const internalAccessToken = context.cookies.get('x-amzn-oidc-data') || process.env.TEST_INTERNAL_ACCESS_TOKEN;
  const url = context.url;

  const protectedStaffRoutes = [/^\/support.*/, /^\/stories.*/];

  console.log("hello 1");
  if (!context.cookies.get("access")?.value) {
    console.log("hello 2");
    if (!internalAccessToken) {
      console.log("hello 3");
      const url = path.join(getBackendUrl(), Routes.APIValidateToken);
      const response = await fetch(url, {
        method: "POST",
        body: JSON.stringify({internal_access_token: internalAccessToken}),
        headers: {"Content-Type": "application/json"}
      });
      
      const data = await response.json();
      console.log("response=", data);
      
      if (data.access) {
        context.cookies.set("access", data.access, { path: "/", sameSite: "lax" });
        context.cookies.set("sessionId", data.sessionId, { path: "/", sameSite: "lax" });
        const resp = await fetchBackendApi<{ is_staff: Boolean }>(
          context,
          Routes.ApiUser,
        );
        userIsStaff = Boolean(resp.is_staff);
      } else {
        context.redirect(Routes.SignInError);
      }
    } else {
      context.redirect(Routes.SignInError);
    }
  }

  for (const protectedStaffRoute of protectedStaffRoutes) {
    if (protectedStaffRoute.test(url.pathname) && !userIsStaff) {
      return context.redirect(Routes.Home);
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
    /^\/evaluations\/[A-Za-z0-9-]*\/questions[/]?$/,
    /^\/support\/users[/]?$/,
    /^\/support\/users\/[A-Za-z0-9]*[/]?$/,
    /^\/support\/users\/new[/]?$/,
    /^\/support\/consultations[/]?$/,
    /^\/support\/consultations\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}[/]?$/,
    /^\/support\/consultations\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\/delete[/]?$/,
    /^\/support\/consultations\/import-summary[/]?$/,
    /^\/support\/consultations\/import-consultation[/]?$/,
    /^\/support\/consultations\/[A-Za-z0-9-]*\/export[/]?$/,
    /^\/design.*/,
    /^\/stories.*/,
    /^\/_astro.*/,
    /^\/api\/validate-token[/]?$/,
  ];

  for (const skipPattern of toSkip) {
    if (skipPattern.test(context.url.pathname)) {
      return next();
    }
  }

  const hasBody = !["GET", "HEAD", "DELETE"].includes(context.request.method);
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
      return context.redirect(Routes.SignInError);
    }

    if (response.status === 304) {
      return response;
    }

    if (response.status === 204) {
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