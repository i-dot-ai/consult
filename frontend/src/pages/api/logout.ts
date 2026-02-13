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

  // Clear ALB auth cookies
  cookies.delete("AWSALBAuthNonce", { path: "/" });
  cookies.delete("X-Amzn-Oidc-Data-0", { path: "/" });

  // Redirect to SSO sign-out with to_client parameter
  // Using to_client (not client_id) triggers immediate session clear and redirect back to app_url
  const ssoSignOutUrl = `https://sso.service.security.gov.uk/sign-out?to_client=${encodeURIComponent(clientId)}`;
  return redirect(ssoSignOutUrl, 302);
};
