import { request as apirequest } from "@playwright/test";
import type { APIRequestContext, Page } from "@playwright/test";
import { S3Client } from "@aws-sdk/client-s3";

import {
  testAccessToken,
  MINIO_ENDPOINT,
  MINIO_ACCESS_KEY,
  MINIO_SECRET_KEY,
} from "../constants";
import type { Fixture, FixtureReference } from "../fixtures";

async function getToken(context: APIRequestContext) {
  const token_response = await context.fetch("/api/validate-token/", {
    method: "POST",
    data: JSON.stringify({
      internal_access_token: testAccessToken,
    }),
    headers: { "Content-Type": "application/json" },
  });

  if (!token_response.ok())
    throw new Error(`Authentication failed: ${token_response.status()}
    ${await token_response.text()}`);

  const data = await token_response.json();
  return { sessionId: data.sessionId, accessToken: data.access };
}

async function fetchApi(
  context: APIRequestContext,
  authData: { sessionId: string; accessToken: string },
  url: string,
  method: string,
  data?: unknown,
) {
  return context.fetch(url, {
    method,
    headers: {
      Cookie: `sessionId=${authData.sessionId}; accessToken=${authData.accessToken}`,
      "Content-Type": "application/json",
    },
    ...(data !== undefined ? { data: JSON.stringify(data) } : {}),
  });
}

/**
 * Sets up test fixtures using dummy data
 */
export async function createFixtureData(
  context: APIRequestContext,
  fixtureData: Fixture,
) {
  const authData = await getToken(context);
  const fixture_response = await fetchApi(
    context,
    authData,
    "/api/consultations/create-test-data/",
    "POST",
    { fixtures: fixtureData },
  );

  if (!fixture_response.ok())
    throw new Error(`Fixture setup failed: ${fixture_response.status()}
    ${await fixture_response.text()}`);

  return await fixture_response.json();
}

/**
 * Tears down test fixtures using dummy data
 */
export async function deleteFixtureData(fixtureData: Fixture) {
  const context = await apirequest.newContext();
  const authData = await getToken(context);
  const fixture_response = await fetchApi(
    context,
    authData,
    "/api/consultations/delete-test-data/",
    "POST",
    { fixtures: fixtureData },
  );

  if (!fixture_response.ok())
    throw new Error(`Fixture deletion failed: ${fixture_response.status()}
    ${await fixture_response.text()}`);
}

/**
 * Adds a new user by email and optionally adds them to a consultation, returns the new user's ID
 */
export async function addUser(email: string, consultationId?: string) {
  const context = await apirequest.newContext();
  const authData = await getToken(context);
  const response = await fetchApi(context, authData, "/api/users/", "POST", { email });

  if (!response.ok())
    throw new Error(`User creation failed: ${response.status()}`)

  const data = await response.json();
  if (!data || !data.id)
    throw new Error(`User creation response missing ID: ${JSON.stringify(data)}`);

  if (consultationId) {
    const add_response = await fetchApi(
      context,
      authData,
      `/api/consultations/${consultationId}/add-users/`,
      "POST",
      { emails: [email] },
    );

    if (!add_response.ok())
      throw new Error(`Adding user to consultation failed: ${add_response.status()}`);
  }

  return data.id;
}

/**
 * Tears down user by email
 */
export async function deleteUser(email: string) {
  const context = await apirequest.newContext();
  const authData = await getToken(context);
  const response = await fetchApi(context, authData, `/api/users/?email=${email}`, "GET");

  if (!response.ok())
    throw new Error(`Failed to retrieve user ID: ${response.status()}`)

  const data = await response.json();

  if (!data?.results?.length || !data.results[0].id)
    return; // No user found, nothing to delete

  const id = data.results[0].id;

  const fixture_response = await fetchApi(context, authData, `/api/users/${id}/`, "DELETE");

  if (!fixture_response.ok())
    throw new Error(`User deletion failed: ${fixture_response.status()}
    ${await fixture_response.text()}`);
}

interface CleanupManagerOptions {
  maxAttempts?: number;
  attemptFrequency?: number;
}

export class CleanupManager {
  private fixtures: FixtureReference[] = [];
  public maxAttempts: number;
  public attemptFrequency: number;

  constructor({ maxAttempts, attemptFrequency }: CleanupManagerOptions = {}) {
    this.maxAttempts = maxAttempts || 5;
    this.attemptFrequency = attemptFrequency || 1000;
  }

  private async _attemptCleanup(maxAttempts: number, attemptFrequency: number, fixture: FixtureReference) {
    let success = false;

    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        await deleteFixtureData(fixture);
        success = true;
        break;
      } catch {
        await new Promise(resolve => setTimeout(resolve, attemptFrequency));
      }
    }

    if (!success) {
      console.error(
        "Test fixture cleanup failed for these consultations: ",
        fixture.consultation_ids?.join(", "),
      );
    }
  }

  add(fixture: FixtureReference) {
    this.fixtures.push(fixture);
  }

  reset() {
    this.fixtures = [];
  }

  async cleanup() {
    for (const fixture of this.fixtures) {
      await this._attemptCleanup(this.maxAttempts, this.attemptFrequency, fixture);
    }
    this.reset();
  }
}

/**
 * Builds an S3 client pointed at the local minio instance. Playwright runs on
 * the host, so this uses the host-reachable endpoint (localhost:9100), with
 * path-style addressing as minio requires.
 */
export function makeMinioClient(): S3Client {
  return new S3Client({
    endpoint: MINIO_ENDPOINT,
    region: "us-east-1",
    forcePathStyle: true,
    credentials: {
      accessKeyId: MINIO_ACCESS_KEY,
      secretAccessKey: MINIO_SECRET_KEY,
    },
  });
}

/**
  * Goes to a specific question in a consultation
 */
export async function goToConsultationQuestion(page: Page, consultationId: string, questionID: string) {
    await page.goto(`/consultations/${consultationId}`);
    await page.waitForLoadState('networkidle');
    await page.goto(`consultations/${consultationId}/questions/${questionID}`);
    await page.waitForLoadState('networkidle');
}
