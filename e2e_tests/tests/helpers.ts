import { request as apirequest } from "@playwright/test";
import type { Page, APIRequestContext } from "@playwright/test";

import { testAccessToken } from "../constants";
import type { Fixture } from "../fixtures";

async function getToken(context: APIRequestContext) {
  const token_response = await context.fetch("/api/validate-token/", {
    method: "POST",
    data: JSON.stringify({
      internal_access_token: testAccessToken,
    }),
    headers: { "Content-Type": "application/json" },
  });

  if (!token_response.ok())
    throw new Error(`Authentication failed: ${token_response.status}
    ${await token_response.text()}`);

  const data = await token_response.json();
  return { sessionId: data.sessionId, accessToken: data.access };
}

/**
 * Sets up test fixtures using dummy data
 */
export async function createFixtureData(
  context: APIRequestContext,
  fixtureData: Fixture,
) {
  const authData = await getToken(context);
  const fixture_response = await context.fetch(
    "/api/consultations/create-test-data/",
    {
      method: "POST",
      headers: {
        Cookie: `sessionId=${authData.sessionId}; accessToken=${authData.accessToken}`,
        "Content-Type": "application/json",
      },
      data: JSON.stringify({ fixtures: fixtureData }),
    },
  );

  if (!fixture_response.ok())
    throw new Error(`Fixture setup failed: ${fixture_response.status}
    ${await fixture_response.text()}`);

  return await fixture_response.json();
}

/**
 * Tears down test fixtures using dummy data
 */
export async function deleteFixtureData(fixtureData: Fixture) {
  const context = await apirequest.newContext();
  const authData = await getToken(context);
  const fixture_response = await context.fetch(
    "/api/consultations/delete-test-data/",
    {
      method: "POST",
      headers: {
        Cookie: `sessionId=${authData.sessionId}; accessToken=${authData.accessToken}`,
        "Content-Type": "application/json",
      },
      data: JSON.stringify({ fixtures: fixtureData }),
    },
  );

  if (!fixture_response.ok())
    throw new Error(`Fixture deletion failed: ${fixture_response.status}
    ${await fixture_response.text()}`);
}

/**
 * Tears down user by email
 */
export async function deleteUser(email: string) {
  const context = await apirequest.newContext();
  const authData = await getToken(context);

  // Retrieve user ID by email
  const response = await context.fetch(`/api/users/?email=${email}`, {
    method: "GET",
    headers: {
      Cookie: `sessionId=${authData.sessionId}; accessToken=${authData.accessToken}`,
      "Content-Type": "application/json",
    },
  });

  if (!response.ok())
    throw new Error(`Failed to retrieve user ID: ${response.status}`)

  const data = await response.json();
  if (!data?.results?.length || !data.results[0].id)
    throw new Error(`No user found with email: ${email}`);

  const id = data.results[0].id;

  const fixture_response = await context.fetch(`/api/users/${id}/`, {
    method: "DELETE",
    headers: {
      Cookie: `sessionId=${authData.sessionId}; accessToken=${authData.accessToken}`,
      "Content-Type": "application/json",
    },
  });

  if (!fixture_response.ok())
    throw new Error(`User deletion failed: ${fixture_response.status}
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
