import { test, expect } from "@playwright/test";
import {
  createFixtureData,
  deleteFixtureData,
} from "./helpers";
import { analysisConsultation } from "../fixtures";
import type { FixtureReference } from "../fixtures";

test.describe("Dashboard Page", () => {
  let testData: FixtureReference = {};
  let consultationId: string;
  let questionIds: string[];

  test.beforeAll(async ({ request }) => {
    testData = await createFixtureData(request, {
      consultations: [analysisConsultation],
    });
  });

  test.beforeEach(async ({ page }) => {
    consultationId = testData.consultation_ids![0];
    questionIds = testData.question_ids!;

    await page.goto(`/consultations/${consultationId}`);
    await page.waitForLoadState("networkidle");
  });

  test("all question cards should show as links", async ({ page }) => {
    for (let questionId of questionIds) {
      const questionCard = page.getByTestId(`question-link-${questionId}`);
      await expect(questionCard.first()).toBeVisible({ timeout: 10000 });

      const questionCardCount = await questionCard.count();
      
      expect(questionCardCount).toBe(1);
    }
  });

  test("metric counts should be as expected", async ({ page }) => {
    const numberOfQuestions = analysisConsultation.questions!.length.toString();
    const numberOfResponses = analysisConsultation.questions!.reduce((sum, question) => sum + (question.responses ? question.responses.length : 0), 0).toString();

    const questionOnPage = page.getByTestId("metric-count-questions");
    await expect (questionOnPage).toBeVisible({ timeout: 10000 });
    await expect (questionOnPage).toHaveText(numberOfQuestions);

    const responsesOnPage = page.getByTestId("metric-count-responses");
    await expect (responsesOnPage).toBeVisible({ timeout: 10000 });
    await expect (responsesOnPage).toHaveText(numberOfResponses);

    const demographicsOnPage = page.getByTestId("metric-count-demographics");
    await expect (demographicsOnPage).toBeVisible({ timeout: 10000 });
    await expect (demographicsOnPage).toHaveText("2");
  });

  test("favourited questions should appear in favourites section", async ({ page }) => {
    for (let questionId of questionIds) {
      const questionFavouriteButton = page.getByTestId(`favourite-button-${questionId}`);
      await expect(questionFavouriteButton.first()).toBeVisible({ timeout: 10000 });
      const favouriteButtonCount = await questionFavouriteButton.count();
      expect(favouriteButtonCount).toBe(1);

      await questionFavouriteButton.click();

      const questionSection = page
      .getByTestId("favourite-questions-section")
      .filter({ has: page.getByTestId(`favourite-button-${questionId}`)})

      await expect (questionSection).toHaveCount(1);
    }
  });

  test.afterAll(async () => {
    await deleteFixtureData(testData);
  });
});
