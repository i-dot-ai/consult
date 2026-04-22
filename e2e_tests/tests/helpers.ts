import type { Page, APIRequestContext } from "@playwright/test";

import { testAccessToken } from "../constants";

/**
 * Sets up test consultations using dummy data
 */
export async function createConsultationData(context: APIRequestContext) {
  const token_response = await context.fetch("/api/validate-token/", {
    method: "POST",
    data: JSON.stringify({
      internal_access_token: testAccessToken,
    }),
    headers: { "Content-Type": "application/json" },
  });

  if (!token_response.ok)
    throw new Error(`Authentication failed: ${token_response.status}
    ${await token_response.text()}`);

  const data = await token_response.json();
  const authData = { sessionId: data.sessionId, accessToken: data.access };

  const fixture_response = await context.fetch(
    "/api/consultations/generate-test-consultation/",
    {
      method: "POST",
      headers: {
        Cookie: `sessionId=${authData.sessionId}; accessToken=${authData.accessToken}`,
      },
    },
  );

  if (!fixture_response.ok)
    throw new Error(`Fixture setup failed: ${fixture_response.status}
    ${await fixture_response.text()}`);
}

/**
 * Finds the first consultation link that points to an actual consultation detail page
 * (not the consultations list page itself)
 */
export async function getFirstConsultationLink(page: Page) {
  const allLinks = page.locator('a[href*="/consultations/"]');
  const count = await allLinks.count();

  for (let i = 0; i < count; i++) {
    const link = allLinks.nth(i);
    const href = await link.getAttribute("href");
    if (href && href !== "/consultations" && !href.endsWith("/consultations")) {
      return { link, href };
    }
  }
  return null;
}
