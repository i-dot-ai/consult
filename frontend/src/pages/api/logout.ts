import type { APIRoute } from "astro";

import { getBackendUrl, getHomepageUrl } from "../../global/utils";

const handleLogout: APIRoute = async (context) => {
  const backendUrl = getBackendUrl();
  const homepageUrl = getHomepageUrl();

  // 1. Call Django logout to clear backend session
  try {
    const cookieHeader = context.request.headers.get("cookie") || "";
    await fetch(`${backendUrl}/api/logout/`, {
      method: "POST",
      headers: {
        cookie: cookieHeader,
      },
    });
  } catch (e) {
    console.error("Error calling backend logout:", e);
  }

  // 2. Call SSO provider to sign out (server-to-server, no CORS issues)
  try {
    await fetch("https://sso.service.security.gov.uk/sign-out", {
      method: "GET",
    });
  } catch (e) {
    console.error("Error calling SSO logout:", e);
  }

  // 3. Clear cookies by setting them as expired
  const cookiesToClear = [
    "accessToken",
    "access",
    "AWSALBAuthNonce",
    "AWSALBAuthSessionCookie",
    "AWSALBAuthSessionCookie-0",
    "AWSALBAuthSessionCookie-1",
    "gds_internal_access",
    "gdsInternalAccess",
    "sessionId",
    "csrftoken",
    "x-amzn-oidc-data",
  ];

  // Also clear X-Amzn-Oidc-Data numbered variants
  for (let i = 0; i < 10; i++) {
    cookiesToClear.push(`X-Amzn-Oidc-Data-${i}`);
  }

  const expiredCookies = cookiesToClear.map(
    (name) => `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/`
  );

  // 4. Return redirect response with cookie clearing headers
  return new Response(null, {
    status: 302,
    headers: {
      Location: homepageUrl,
      "Set-Cookie": expiredCookies.join(", "),
    },
  });
};

// Support both GET (navigation) and POST (fetch)
export const GET: APIRoute = handleLogout;
export const POST: APIRoute = handleLogout;
