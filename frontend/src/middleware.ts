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
