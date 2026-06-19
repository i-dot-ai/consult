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
    const titleText = page.getByRole("heading", { name: "Detailed Consultation Analysis" });
    await expect(titleText).toBeVisible();

    const backButton = page.getByTestId("back-button");
    await expect(backButton).toBeVisible();
    await backButton.click()

    await expect(page).toHaveURL(/\/consultations\/.*/);
  });

  test("demographics summaries should have expected text", async ({ page }) => {
    // assertion here is based on a snapshot of what is displayed
    // it will need updating if we change the fixture data

    const ageGroup = page.getByTestId('metrics-summary-age_group');
    await expect(ageGroup).toBeVisible();

    const ageGroupText = ageGroup.getByTestId('panel-component');
    await expect (ageGroupText).toHaveText("age_group 18-35 2 40% 36-50 2 40% 51-65 1 20%  ", );

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

  test("demographic chart has expected labels", async ({ page }) => {
    const q1Text = page.locator("#legend-id1");
    await expect(q1Text).toHaveText("Don't know16.7%(1)No33.3%(2)No answer0%(0)Yes50%(3)");

    const q3Text = page.locator("#legend-id3");
    await expect(q3Text).toHaveText("Brand recognition0%(0)Cost-effectiveness20%(2)Design30%(3)Durability30%(3)Sustainability20%(2)");
  });

  test.afterAll(async () => {
    await deleteFixtureData(testData);
  });
});
