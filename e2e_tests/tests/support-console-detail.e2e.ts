import { test, expect } from "@playwright/test";
import { CleanupManager, createFixtureData } from "./helpers";

import {
  defaultUser,
  setupConsultation,
  signOffConsultation,
} from "../fixtures";

import type { FixtureReference } from "../fixtures";

test.describe("Support Console - Consultations Detail", () => {
  let testData: FixtureReference = {};
  const cleanupManager = new CleanupManager();

  test.beforeAll(async ({ request }) => {
    testData = await createFixtureData(request, {
      consultations: [setupConsultation, signOffConsultation],
    });
    cleanupManager.add(testData);
  });

  test.beforeEach(async ({ page }) => {
    await page.goto("/support/consultations");
    await page.waitForLoadState("networkidle");

    await page.getByRole("button", { name: setupConsultation.title }).first().click();
  });

  test("displays consultation title", async ({ page }) => {
    // Check the page heading
    await expect(page.getByRole("heading", { name: setupConsultation.title })).toBeVisible();
  })

  const NAV_LINKS = [
    { text: "View on frontend (question review)", url: new RegExp("/evaluations/.*/questions/") },
    { text: "View finalise theme", url: new RegExp("/consultations/.*/finalising-themes") },
    { text: "View on frontend (dashboard)", url: new RegExp("/consultations/.*") },
    { text: "Import finalised themes from another consultation", url: new RegExp("/support/consultations/.*/import-themes") },
    { text: "Delete this consultation", url: new RegExp("/support/consultations/.*/delete") },
  ]
  
  NAV_LINKS.forEach(({ text, url }) => {
    test(`displays nav link: ${text}`, async ({ page }) => {
      // Check the page heading
      const link = page.getByRole("button", { name: text });
      await link.click();
      expect(page).toHaveURL(url);
    })
  })

  test(`displays user email`, async ({ page }) => {
    const userButton = page.getByRole("button", { name: defaultUser.email });
    await expect(userButton).toBeVisible();
    await userButton.click();
    await expect(page).toHaveURL(new RegExp("/support/users/.*"));
  })

  test(`displays remove user link`, async ({ page }) => {
    const removeUserButton = page.getByRole("button", { name: "remove" });
    await expect(removeUserButton).toBeVisible();

    await removeUserButton.click();
    await expect(page).toHaveURL(new RegExp("/support/consultations/.*/users/.*/remove"));
  })

  test.afterAll(async () => {
    await cleanupManager.cleanup();
  });
});
