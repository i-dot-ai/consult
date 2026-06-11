import { test, expect } from "@playwright/test";
import {
  createFixtureData,
  deleteFixtureData,
} from "./helpers";
import { signedOffConsultation } from "../fixtures";
import type { FixtureReference } from "../fixtures";

test.describe("Question Detail Page", () => {
  let testData: FixtureReference = {};
  let consultationId: string;
  let questionIds: string[];

  test.beforeAll(async ({ request }) => {
    testData = await createFixtureData(request, {
      consultations: [signedOffConsultation],
    });
    consultationId = testData.consultation_ids![0];
    questionIds = testData.question_ids!;
  });

  test.beforeEach(async ({ page }) => {
    await page.goto(
      `/consultations/${consultationId}/finalising-themes/${questionIds[0]}`
    );
    await page.waitForLoadState("networkidle");
  });

  test("page navigation should work correctly", async ({ page }) => {
    const backButton = page.getByTestId("back-button");
    await expect(backButton).toBeVisible();

    await expect(page).toHaveURL(/\/consultations\/.*\/finalising-themes\/.*/);
  });

  test("select another question should work correctly", async ({ page }) => {
    const selectAnotherQuestion = page.getByRole("button", { name: "Select Another Question" })
    await expect(selectAnotherQuestion).toBeVisible();

    await expect(page).toHaveURL(/\/consultations\/.*\/finalising-themes\/.*/);
  });

  test("question status is signed off", async ({ page }) => {
    const status = page.getByTestId("themes-finalised-pill").locator("div").filter({ hasText: "Themes finalised" });
    await expect(status).toHaveCount(1);
    await expect(status).toBeVisible();
  });


  test.afterAll(async () => {
    await deleteFixtureData(testData);
  });
});
