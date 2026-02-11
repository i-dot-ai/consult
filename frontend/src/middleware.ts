import type { APIContext, MiddlewareHandler, MiddlewareNext } from "astro";
import { Routes } from "./global/routes";
import { fetchBackendApi } from "./global/api";
import { getBackendUrl, getEnv } from "./global/utils";

export const onRequest: MiddlewareHandler = async (
  context: APIContext,
  next: MiddlewareNext,
) => {
  const url = context.url;
  const backendUrl = getBackendUrl();

  // Skip authentication for /api/* routes - handled by the API proxy
  if (/^\/api\//.test(url.pathname)) {
    return next();
  }

  // Skip authentication for /health - handled by frontend health check
  if (/^\/health[/]?$/.test(url.pathname)) {
    return next();
  }

  let internalAccessToken = null;
  let userIsStaff = false;

  const env = getEnv().toLowerCase();
  const protectedStaffRoutes = [/^\/support.*/, /^\/stories.*/];

  // Check for test env and load dummy token
  if (env === "local" || env === "test" || env == null) {
    internalAccessToken =
      process.env.TEST_INTERNAL_ACCESS_TOKEN ||
      import.meta.env?.TEST_INTERNAL_ACCESS_TOKEN;
  } else {
    internalAccessToken = context.request.headers.get("x-amzn-oidc-data");
  }

  // Validate token with the backend
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

  // Check if user is staff for protected routes
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

  // ===== NOW RENDER THE PAGE =====
  const response = await next();

  // Add security headers to response
  const EXTRA_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy":
      "camera=(), microphone=(), geolocation=(), payment=()",
    "X-Frame-Options": "DENY",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
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
