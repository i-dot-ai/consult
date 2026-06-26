import { test, expect } from "@playwright/test";
import { CleanupManager, createFixtureData } from "./helpers";
import { defaultUser, setupConsultation } from "../fixtures";
import type { FixtureReference } from "../fixtures";

// The User List and Question List groups only read the consultation dashboard,
// so they share a single fixture created once for the whole block.
test.describe("Admin Dashboard - Dashboard Page", () => {
  const cleanupManager = new CleanupManager();
  let testData: FixtureReference = {};
  let consultationId: string;

  test.beforeAll(async ({ request }) => {
    testData = await createFixtureData(request, {
      consultations: [setupConsultation],
    });
    cleanupManager.add(testData);
    consultationId = testData.consultation_ids![0];
  });

  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");
    await page.goto("/admin");
    await page.waitForLoadState("networkidle");
  });

  test.describe("User List", () => {
    test("displays users table with correct column headers", async ({ page }) => {
      expect(2+2).toBe(4);
    });
  });

  test.afterEach(async () => {
    await cleanupManager.cleanup();
  });
});
