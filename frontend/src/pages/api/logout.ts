import type { APIRoute } from "astro";

import { getClientId } from "../../global/utils";

export const GET: APIRoute = async ({ cookies, redirect }) => {
  // Get client ID for SSO sign-out
  let clientId = "";
  try {
    clientId = getClientId();
  } catch (e) {
    console.error("Failed to get client ID:", e);
  }

  // Clear all known cookies server-side (including HttpOnly cookies)
  const cookiesToClear = [
    // App cookies
    "gdsInternalAccess",
    "gds_internal_access",
    "sessionId",
    "csrftoken",
    "accessToken",
    "access",
    // ALB cookies
    "AWSALBAuthSessionCookie",
    "AWSALBAuthSessionCookie-0",
    "AWSALBAuthSessionCookie-1",
    "AWSALBAuthNonce",
    // OIDC cookies
    "x-amzn-oidc-data",
  ];

  // Clear numbered OIDC data cookies
  for (let i = 0; i < 10; i++) {
    cookiesToClear.push(`X-Amzn-Oidc-Data-${i}`);
  }

  // Delete each cookie
  for (const cookieName of cookiesToClear) {
    cookies.delete(cookieName, { path: "/" });
  }

  // Redirect to SSO sign-out with to_client parameter
  // Using to_client (not client_id) triggers immediate session clear and redirect back to app_url
  const ssoSignOutUrl = `https://sso.service.security.gov.uk/sign-out?to_client=${encodeURIComponent(clientId)}`;
  return redirect(ssoSignOutUrl, 302);
};
