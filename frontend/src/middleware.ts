import type { APIContext, MiddlewareHandler, MiddlewareNext } from "astro";
import { Routes } from "./global/routes";
import { fetchBackendApi } from "./global/api";
import { getBackendUrl, getEnv } from "./global/utils";

const getCspValue = (): string => {
  return `
    default-src 'self';
    style-src 'self' 'unsafe-inline';
    script-src 'self' 'unsafe-inline';
    img-src 'self' data:;
    font-src 'self' data:;
    connect-src 'self' *.ingest.de.sentry.io;
  `
    .replace(/\n/g, " ")
    .trim();
};

export const onRequest: MiddlewareHandler = async (
  context: APIContext,
  next: MiddlewareNext,
) => {
  const url = context.url;
  const backendUrl = getBackendUrl();

  if (/^\/api\//.test(url.pathname)) {
    return next();
  }

  if (/^\/health[/]?$/.test(url.pathname)) {
    return next();
  }

  // Proxy Django admin and static files without applying frontend security headers
  if (
    /^\/admin(\/|$)/.test(url.pathname) ||
    /^\/django-rq(\/|$)/.test(url.pathname) ||
    /^\/static(\/|$)/.test(url.pathname)
  ) {
    return await proxyToDjango(context, backendUrl);
  }

  let internalAccessToken = null;
  let userIsStaff = false;

  const env = getEnv().toLowerCase();
  const protectedStaffRoutes = [/^\/support.*/, /^\/stories.*/];

  if (env === "local" || env === "test") {
    internalAccessToken =
      process.env.TEST_INTERNAL_ACCESS_TOKEN ||
      import.meta.env?.TEST_INTERNAL_ACCESS_TOKEN;
  } else {
    internalAccessToken = context.request.headers.get("x-amzn-oidc-data");
  }

  if (internalAccessToken) {
    try {
      await validateUserToken(backendUrl, internalAccessToken, context);
    } catch (e: unknown) {
      console.error("Unknown error signing in", e);
      return context.redirect(Routes.SignInError);
    }
  } else {
    console.error("Authentication token not found");
    return context.redirect(Routes.SignInError);
  }

  try {
    const resp = await fetchBackendApi<{ is_staff: boolean }>(
      context,
      Routes.ApiUser,
    );
    userIsStaff = Boolean(resp.is_staff);
  } catch (e) {
    console.error("Error accessing user info", e);
  }

  for (const protectedStaffRoute of protectedStaffRoutes) {
    if (protectedStaffRoute.test(url.pathname) && !userIsStaff) {
      console.error("Redirecting to /");
      return context.redirect(Routes.Home);
    }
  }

  const response = await next();

  const EXTRA_HEADERS: Record<string, string> = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy":
      "camera=(), microphone=(), geolocation=(), payment=()",
    "X-Frame-Options": "DENY",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": getCspValue(),
  };

  for (const [key, value] of Object.entries(EXTRA_HEADERS)) {
    response.headers.set(key, value);
  }

  return response;
};

async function validateUserToken(
  backendUrl: string,
  internalAccessToken: string,
  context: APIContext,
) {
  const validateUrl = new URL(Routes.APIValidateToken, backendUrl).toString();
  const response = await fetch(validateUrl, {
    method: "POST",
    body: JSON.stringify({
      internal_access_token: internalAccessToken,
    }),
    headers: { "Content-Type": "application/json" },
  });
  const data = await response.json();

  context.cookies.set("sessionId", data.sessionId, {
    path: "/",
    sameSite: "strict",
  });
  context.cookies.set("accessToken", data.access, {
    path: "/",
    sameSite: "strict",
  });
}

async function proxyToDjango(context: APIContext, backendUrl: string) {
  const url = context.url;
  const fullBackendUrl = new URL(
    url.pathname + url.search,
    backendUrl,
  ).toString();

  const hasBody = !["GET", "HEAD", "DELETE"].includes(context.request.method);

  try {
    const cookieHeader = context.request.headers.get("cookie") || "";

    let requestBody = undefined;
    if (hasBody) {
      requestBody = await context.request.arrayBuffer();
    }

    const headersToSend = new Headers();

    for (const [key, value] of context.request.headers.entries()) {
      headersToSend.set(key, value);
    }

    // Handle Origin/Referer/Host headers for Django CSRF protection
    // Django CSRF checks that the Origin matches CSRF_TRUSTED_ORIGINS
    //
    // Architecture:
    // - Local dev: frontend (localhost:3000) proxies to backend (localhost:8000)
    //   Origin needs rewriting since they're on different ports
    // - Production: Both use public URL (e.g., https://consult-preprod.ai.cabinetoffice.gov.uk)
    //   Frontend proxies to internal backend URL, but Origin should stay as public URL
    //
    // Strategy: Keep original Origin/Referer unless they explicitly point to localhost
    // on a different port than the backend (local dev scenario)

    const backendUrlObj = new URL(backendUrl);
    const origin = context.request.headers.get("origin");
    const referer = context.request.headers.get("referer");

    // Debug logging for CSRF issues
    if (context.request.method === "POST") {
      console.log("[proxyToDjango] POST request to:", url.pathname);
      console.log("[proxyToDjango] Original Origin:", origin);
      console.log("[proxyToDjango] Original Referer:", referer);
      console.log("[proxyToDjango] Backend URL:", backendUrl);
    }

    // Check if this is local development (localhost with mismatched ports)
    if (origin) {
      const originObj = new URL(origin);
      const isLocalDev =
        originObj.hostname === "localhost" &&
        backendUrlObj.hostname === "localhost" &&
        originObj.port !== backendUrlObj.port;

      if (isLocalDev) {
        // Local dev: rewrite to backend URL
        headersToSend.set("Origin", backendUrl);

        // Also rewrite Referer if present
        if (referer) {
          try {
            const refererUrl = new URL(referer);
            refererUrl.protocol = backendUrlObj.protocol;
            refererUrl.host = backendUrlObj.host;
            headersToSend.set("Referer", refererUrl.toString());
          } catch {
            headersToSend.set("Referer", backendUrl);
          }
        }

        // Set Host header to backend
        headersToSend.set("Host", backendUrlObj.host);
      }
      // Production: Keep original Origin/Referer/Host - they're already correct
    }

    // Debug logging continued
    if (context.request.method === "POST") {
      console.log("[proxyToDjango] Final Origin being sent:", headersToSend.get("Origin"));
      console.log("[proxyToDjango] Final Referer being sent:", headersToSend.get("Referer"));
      console.log("[proxyToDjango] Final Host being sent:", headersToSend.get("Host"));
    }

    const accessToken = context.cookies.get("accessToken")?.value;
    if (accessToken) {
      headersToSend.set("Authorization", `Bearer ${accessToken}`);
    }
    headersToSend.set("Cookie", cookieHeader);

    const csrfCookie = context.cookies.get("csrftoken");
    if (csrfCookie) {
      headersToSend.set("X-CSRFToken", csrfCookie.value);
    }

    const response = await fetch(fullBackendUrl, {
      method: context.request.method,
      headers: headersToSend,
      body: requestBody,
      redirect: "manual",
    });

    const redirectStatuses = [301, 302, 303, 307, 308] as const;
    type RedirectStatus = (typeof redirectStatuses)[number];
    if (redirectStatuses.includes(response.status as RedirectStatus)) {
      const location = response.headers.get("location");
      if (location) {
        return context.redirect(location, response.status as RedirectStatus);
      }
    }

    if (response.status === 401) {
      console.log("Django admin 401 error - redirecting to sign in");
      return context.redirect(Routes.SignInError);
    }

    const body = await response.arrayBuffer();
    const newResponse = new Response(body, {
      status: response.status,
      headers: response.headers,
    });

    return newResponse;
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "unknown";
    console.error("Error proxying to Django:", message);
    return new Response(
      JSON.stringify({ message: "Error connecting to backend" }),
      {
        status: 500,
      },
    );
  }
}
