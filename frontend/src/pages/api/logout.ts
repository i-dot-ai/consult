import type { APIRoute } from "astro";

import { getClientId } from "../../global/utils";

export const GET: APIRoute = async ({ cookies, redirect }) => {
  let clientId = "";
  try {
    clientId = getClientId();
  } catch (e) {
    console.error("Failed to get client ID:", e);
  }

  cookies.delete("AWSALBAuthNonce", { path: "/" });
  cookies.delete("X-Amzn-Oidc-Data-0", { path: "/" });

  const ssoSignOutUrl = `https://sso.service.security.gov.uk/sign-out?to_client=${encodeURIComponent(clientId)}`;
  return redirect(ssoSignOutUrl, 302);
};
