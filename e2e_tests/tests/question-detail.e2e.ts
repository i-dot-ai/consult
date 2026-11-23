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
    // Go straight to a known confirmed question from the signed-off fixture.
    await page.goto(
      `/consultations/${consultationId}/finalising-themes/${questionIds[0]}`,
    );
    await page.waitForLoadState("networkidle");
  });

  test("page navigation should work correctly", async ({ page }) => {
    const backButton = page.getByTestId("back-button");
    await expect(backButton).toBeVisible();
    await backButton.click();

    await expect(page).toHaveURL(/\/consultations\/.*\/finalising-themes/);
  });

  test("select another question should work correctly", async ({ page }) => {
    const backToQuestions = page.getByTestId("back-button");
    await expect(backToQuestions).toBeVisible();
    await backToQuestions.click();

    // Should navigate back to the question list (without the questionId)
    await expect(page).toHaveURL(/\/consultations\/.*\/finalising-themes$/);
  });

  test("question status is signed off", async ({ page }) => {
    await expect(page.getByTestId("themes-finalised-pill")).toBeVisible();
  });


  test.afterAll(async () => {
    await deleteFixtureData(testData);
  });
});
