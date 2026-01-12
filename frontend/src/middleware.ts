import path from "path";

import type { MiddlewareHandler } from "astro";
import { Routes } from "./global/routes";
import { fetchBackendApi } from "./global/api";
import { getBackendUrl } from "./global/utils";

import { internalAccessCookieName } from "./global/api";

export const onRequest: MiddlewareHandler = async (context, next) => {
  let internalAccessToken = null;

  const env = process.env.ENVIRONMENT || import.meta.env?.ENVIRONMENT?.toLowerCase();

  if (env === "local" || env === "test" || env == null) {
    internalAccessToken = process.env.TEST_INTERNAL_ACCESS_TOKEN || import.meta.env?.TEST_INTERNAL_ACCESS_TOKEN;
  } else {
    internalAccessToken = context.request.headers.get("x-amzn-oidc-data");
  }

  const url = context.url;
  const backendUrl = getBackendUrl();
  const protectedStaffRoutes = [/^\/support.*/, /^\/stories.*/];

  if (!context.cookies.get(internalAccessCookieName)?.value) {
    if (internalAccessToken) {
      try {
        const body = JSON.stringify({
          internal_access_token: internalAccessToken,
        });
        const response = await fetch(
          path.join(backendUrl, Routes.APIValidateToken),
          {
            method: "POST",
            body: body,
            headers: { "Content-Type": "application/json" },
          },
        );
        const data = await response.json();

        // Decode JWT to get expiration time
        const jwtPayload = JSON.parse(atob(data.access.split(".")[1]));
        const jwtExpiry = new Date(jwtPayload.exp * 1000); // Convert from Unix timestamp

        context.cookies.set(internalAccessCookieName, data.access, {
          path: "/",
          sameSite: "strict",
          expires: jwtExpiry,
        });
        context.cookies.set("sessionId", data.sessionId, {
          path: "/",
          sameSite: "strict",
        });
      } catch (e: unknown) {
        console.error("sign-in error", e);
        context.redirect(Routes.SignInError);
      }
    } else {
      console.error("internalAccessToken not set", backendUrl);
      context.redirect(Routes.SignInError);
    }
  }

  let userIsStaff = false;
  if (context.cookies.get(internalAccessCookieName)?.value) {
    try {
      const resp = await fetchBackendApi<{ is_staff: boolean }>(
        context,
        Routes.ApiUser,
      );
      userIsStaff = Boolean(resp.is_staff);
    } catch (e) {
      console.error("error accessing user info", e);
    }
  }

  for (const protectedStaffRoute of protectedStaffRoutes) {
    if (protectedStaffRoute.test(url.pathname) && !userIsStaff) {
      console.error("redirecting to home");
      return context.redirect(Routes.Home);
    }
  }

  const fullBackendUrl = path.join(backendUrl, url.pathname) + url.search;

  // skip as new pages are moved to astro
  const toSkip = [
    /^\/$/,
    /^\/data-sharing[/]?$/,
    /^\/get-involved[/]?$/,
    /^\/guidance[/]?$/,
    /^\/privacy[/]?$/,
    /^\/sign-in-error[/]?$/,
    /^\/api\/astro\/.*/,
    /^\/api\/health[/]?$/,
    /^\/health[/]?$/,
    /^\/.well-known\/.*/,
    /^\/consultations.*/,
    /^\/evaluations\/[A-Za-z0-9-]*\/questions[/]?$/,
    /^\/evaluations\/[A-Za-z0-9-]+\/questions\/[A-Za-z0-9-]+\/responses\/[A-Za-z0-9-]+\/?$/,
    /^\/support\/users[/]?$/,
    /^\/support\/users\/[A-Za-z0-9]*[/]?$/,
    /^\/support\/users\/new[/]?$/,
    /^\/support\/consultations[/]?$/,
    /^\/support\/consultations\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}[/]?$/,
    /^\/support\/consultations\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\/delete[/]?$/,
    /^\/support\/consultations\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\/questions\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\/delete[/]?$/,
    /^\/support\/consultations\/import-summary[/]?$/,
    /^\/support\/consultations\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\/users\/new[/]?$/,
    /^\/support\/consultations\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\/users\/[A-Za-z0-9-]+\/remove[/]?$/,
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
        context.cookies.set(
          internalAccessCookieName,
          {},
          {
            path: "/",
            sameSite: "strict",
            expires: new Date(0),
          },
        );
        console.log("stale cokie removed, redirecting home");

        return context.redirect(Routes.Home);
      }
    }

    // Create headers object properly
    const headersToSend = new Headers();

    // Copy all original headers
    for (const [key, value] of context.request.headers.entries()) {
      headersToSend.set(key, value);
    }

    // Add/override specific headers
    const accessToken = context.cookies.get(internalAccessCookieName)?.value;
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
      console.log("Error 401 redirecting to sign in");
      return context.redirect(Routes.SignInError);
    }

    if (response.status === 403) {
      console.log("403 detected", fullBackendUrl, response.body, accessToken);
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
