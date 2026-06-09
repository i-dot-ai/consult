import { test, expect } from "@playwright/test";
import {
  createFixtureData,
  deleteFixtureData,
} from "./helpers";
import { analysisConsultation } from "../fixtures";
import type { FixtureReference } from "../fixtures";

test.describe("Demographic Detail Page", () => {
  let testData: FixtureReference = {};
  let consultationId: string;

  test.beforeAll(async ({ request }) => {
    testData = await createFixtureData(request, {
      consultations: [analysisConsultation],
    });
  });

  test.beforeEach(async ({ page }) => {
    consultationId = testData.consultation_ids![0];

    await page.goto(`/consultations/${consultationId}`);
    await page.waitForLoadState("networkidle");

    const demographicButton = page.getByRole("button", { name: "View All" })

    await demographicButton.click()
    await page.waitForLoadState("networkidle");
  });

  test("page navigation and title should display correctly", async ({ page }) => {
    const backButton = page.getByTestId("back-button");
    await expect(backButton).toBeVisible();

    const titleText = page.getByRole("heading", { name: "Detailed Consultation Analysis" });
    await expect(titleText).toBeVisible();
  });

  test("demographics summaries should have expected text", async ({ page }) => {
    // assertion here is based on a snapshot of what is displayed
    // it will need updating if we change the fixture data

    const ageGroup = page.getByTestId('metrics-summary-age_group');
    await expect(ageGroup).toBeVisible();

    const ageGroupText = ageGroup.getByTestId('panel-component');
    await expect (ageGroupText).toHaveText("age_group 18-35 2 40% 36-50 2 40% 51-65 1 20%  ");

    const nation = page.getByTestId('metrics-summary-nation');
    await expect(nation).toBeVisible();

    const nationText = nation.getByTestId('panel-component');
    await expect (nationText).toHaveText("nation England 2 40% Northern Ireland 1 20% Scotland 1 20% Wales 1 20%  ");
  });

  test("demographic chart item should strikethrough on click", async ({ page }) => {
    const yesItemText = page.getByTestId('chart-legend-item-container-Yes');
    await expect(yesItemText).not.toContainClass("line-through");

    const yesItemClickable = page.getByTestId('chart-legend-item-clickable-Yes');
    await yesItemClickable.click();
    
    await expect(yesItemText).toContainClass("line-through");
  });

  test.afterAll(async () => {
    await deleteFixtureData(testData);
  });
});
