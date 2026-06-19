import { test, expect } from "@playwright/test";
import { CleanupManager, createFixtureData } from "./helpers";

import {
  defaultUser,
  setupConsultation,
  signOffConsultation,
} from "../fixtures";

import type { FixtureReference } from "../fixtures";


test.describe("Support Console - Users Detail", () => {
  let testData: FixtureReference = {};
  const cleanupManager = new CleanupManager();

  test.beforeAll(async ({ request }) => {
    testData = await createFixtureData(request, {
      consultations: [setupConsultation, signOffConsultation],
    });
    cleanupManager.add(testData);
  });

  test.beforeEach(async ({ page }) => {
    await page.goto("/support/users");
    await page.waitForLoadState("networkidle");

    await page.getByRole("button", { name: defaultUser.email }).first().click();
  });

  test("displays user email as heading", async ({ page }) => {
    // Check the page heading
    await expect(page.getByRole("heading", { name: defaultUser.email })).toBeVisible();
  })

  test("displays created at", async ({ page }) => {
    // Check the page heading
    const createdAtCell = page.getByTestId("created-at-value");
    await expect(createdAtCell).toBeVisible();
    // regex matches single or double digit days or months and
    // double or quadruple years
    await expect(createdAtCell).toHaveText(/^\d?\d\/\d?\d\/\d?\d?\d\d$/);
  })

  test.afterAll(async () => {
    await cleanupManager.cleanup();
  });
});
