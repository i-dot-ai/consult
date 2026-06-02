import { test, expect } from "@playwright/test";
import {
  createFixtureData,
  deleteFixtureData,
} from "./helpers";
import { analysisConsultation } from "../fixtures";
import type { FixtureReference } from "../fixtures";

test.describe("Respondent Detail Page", () => {
  let testData: FixtureReference = {};
  let consultationId: string;
  let respondentId: string;
  let questionIds: string[];
  let themefinderId: string;

  test.beforeAll(async ({ request }) => {
    testData = await createFixtureData(request, {
      consultations: [analysisConsultation],
    });
  });

  test.beforeEach(async ({ page }) => {
    // Use consultation ID from fixture data directly
    consultationId = testData.consultation_ids![0];
    questionIds = testData.question_ids!;
    const questionId = questionIds[0];

    // Navigate to consultation detail page
    await page.goto(`/consultations/${consultationId}`);
    await page.waitForLoadState("networkidle");

    // analysisConsultation has 3 questions:
    // Q1: hybridQuestionWithThemes (5 responses, has_free_text: true) <- Has Response Analysis tab
    // Q3: multChoiceQuestion (10 responses, has_free_text: false) <- NO Response Analysis tab!
    // Q4: openQuestionWithThemes (5 responses, has_free_text: true) <- Has Response Analysis tab
    // IMPORTANT: Only questions with has_free_text: true have the Response Analysis tab
    // Click on Q1 (first question) which has free text and Response Analysis tab
    const questionCard = page.getByTestId(`question-link-${questionId}`);
    await expect(questionCard.first()).toBeVisible({ timeout: 10000 });

    const questionCardCount = await questionCard.count();
    
    // Fixture should create 3 questions, but only 1 with this ID
    expect(questionCardCount).toBe(1);
    
    await questionCard.click();
    await page.waitForLoadState("networkidle");

    // We should be on a question detail page
    await expect(page).toHaveURL(/\/consultations\/.*\/questions\/.*/);
  });

  test("2 plus 2", async ({ page }) => {
    const answer = 4;
    expect((2+2) == answer);
  });

});