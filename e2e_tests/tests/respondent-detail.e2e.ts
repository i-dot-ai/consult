import { test, expect } from "@playwright/test";
import {
  createFixtureData,
  deleteFixtureData,
} from "./helpers";
import { analysisConsultation, hybridQuestion } from "../fixtures";
import type { FixtureReference } from "../fixtures";

test.describe("Respondent Detail Page", () => {
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
    const questionId = questionIds[0];

    await page.goto(`/consultations/${consultationId}`);
    await page.waitForLoadState("networkidle");

    const questionCard = page.getByTestId(`question-link-${questionId}`);
    await expect(questionCard.first()).toBeVisible({ timeout: 10000 });

    const questionCardCount = await questionCard.count();
    
    expect(questionCardCount).toBe(1);
    
    await questionCard.click();
    await page.waitForLoadState("networkidle");

    await expect(page).toHaveURL(/\/consultations\/.*\/questions\/.*/);

    const allRespondentButtons = page.getByTestId('respondent-button');

    await expect(allRespondentButtons.first()).toBeVisible({ timeout: 10000 });

    const respondentCount = await allRespondentButtons.count();
    
    expect(respondentCount).toBeGreaterThan(0);

    const respondentButton = allRespondentButtons.first();

    await respondentButton.click();
    await page.waitForLoadState("networkidle");

    await expect(page).toHaveURL(/\/consultations\/.*\/respondent\/.*/);
    
    await expect(page.getByRole("heading", { name: /responses to consultation questions/i })).toBeVisible({ timeout: 10000 });
    
    const loadingMessage = page.getByText("Loading Responses...");
    await expect(loadingMessage).toBeHidden({ timeout: 30000 });

    await expect(page.getByTestId('question-number').first()).toBeVisible({ timeout: 10000 });

    const currentUrl = page.url();
    const urlMatch = currentUrl.match(
      /\/consultations\/([^/]+)\/respondent\/([^?]+)/,
    );
    expect(urlMatch).toBeTruthy();
    respondentId = urlMatch![2];

    const url = new URL(currentUrl);
    themefinderId = url.searchParams.get("themefinder_id") || "";
  });

  test("page navigation and title should display correctly", async ({ page }) => {
    const backButton = page.getByTestId("back-to-analysis-button");
    await expect(backButton).toBeVisible();

    const prevButton = page
      .getByRole("button", { name: /previous/i })
      .or(page.getByRole("link", { name: /previous/i }));
    const nextButton = page
      .getByRole("button", { name: /next/i })
      .or(page.getByRole("link", { name: /next/i }));
    
    const navigationButtons = prevButton.or(nextButton);
    await expect(navigationButtons.first()).toBeVisible();
  });

  test("sidebar shows correct information", async ({ page }) => {
    const sidebarHeading = page
      .getByRole("heading", { name: /respondent demographics/i })
      .or(page.getByText(/demographics/i));
    await expect(sidebarHeading.first()).toBeVisible();

    const stakeholderLabel = page.getByText(/stakeholder name/i);
    await expect(stakeholderLabel.first()).toBeVisible();
  });

  test("sidebar answered percentage should be correct", async ({ page }) => {
    await page.waitForLoadState("networkidle");

    const questionsAnswered = page.getByText(/questions answered/i);
    const questionsAnsweredCount = await questionsAnswered.count();
    
    expect(questionsAnsweredCount).toBeGreaterThan(0);

    await expect(questionsAnswered.first()).toBeVisible();

    const progressText = await page.getByTestId('questions-answered-progress').textContent();
    
    const progressSplit = progressText?.split(" ");

    expect(progressSplit ? progressSplit.length : 0).toBeGreaterThan(0);

    const percentage = parseInt(progressSplit![0].replace("%", ""));
    const fraction = progressSplit![1].split("/");
    const answered = parseInt(fraction![0].replace("(", ""));
    const total = parseInt(fraction![1].replace(")", ""));

    expect(answered).toBeLessThanOrEqual(total);
    expect(total).toBeGreaterThan(0);

    expect(total).toBe(3);

    const calculatedPercentage = Math.round((answered / total) * 100);
    expect(percentage).toBe(calculatedPercentage);
  });

  test("displays responses section with heading", async ({ page }) => {
    const responsesHeading = page
      .getByRole("heading", {
        name: /responses to consultation questions/i,
      })
      .or(page.getByText(/responses to consultation/i));
    await expect(responsesHeading.first()).toBeVisible();

    const subtitle = page.getByText(/all responses submitted/i);
    await expect(subtitle.first()).toBeVisible();
  });

  test("displays individual response cards with question numbers", async ({
    page,
  }) => {
    await page.waitForLoadState("networkidle");
    const questionBadges = page.getByTestId('question-number');
    await expect(questionBadges.first()).toBeVisible({ timeout: 15000 });
    const questionLinks = page.locator('a[href*="/questions/"]');
    await expect(questionLinks.first()).toBeVisible();
  });

  test("displays response text for answered questions", async ({ page }) => {
    await page.waitForLoadState("networkidle");

    const responseTexts = page.getByTestId('response-text');
    
    await expect(responseTexts.filter({visible: true}).first()).toBeVisible({ timeout: 15000 });
    
    const count = await responseTexts.count();
    expect(count).toBeGreaterThan(0);
    
    for (let i = 0; i < count; i++) {
      await expect(responseTexts.nth(i)).toBeAttached();
    }
    
    const allResponseTexts = await responseTexts.allTextContents();
    for (const text of allResponseTexts) {
      expect(text.trim().length).toBeGreaterThan(0);
    }
  });

  test("displays themes for responses with assigned themes", async ({
    page,
  }) => {
    await page.waitForLoadState("networkidle");

    const themesLabel = page.getByText(/themes:/i);
    await expect(themesLabel.first()).toBeVisible({ timeout: 15000 });

    const themeTags = page.getByText("Standardized framework").or(page.getByText("Innovation"));

    await expect(themeTags.first()).toBeVisible({ timeout: 15000 });
  });

  test("displays evidence-rich badge for qualifying responses", async ({
    page,
  }) => {
    await page.waitForLoadState("networkidle");
    const evidenceBadge = page.getByTestId("evidence-rich-badge");
    await expect(evidenceBadge.first()).toBeVisible({timeout: 15000});
  });

  test("displays multiple choice responses when answered", async ({ page }) => {
    await page.waitForLoadState("networkidle");

    const multipleChoiceLabel = page.getByText(/multiple choice response/i);
    await expect(multipleChoiceLabel.first()).toBeVisible();

    const multipleChoiceOptions = page.getByTestId('multiple-choice-options');
    await expect(multipleChoiceOptions.first()).toBeVisible();
    
    const allOptionsTexts = await multipleChoiceOptions.allTextContents();
    const combinedOptionsText = allOptionsTexts.join(' ');
    
    expect(combinedOptionsText).toMatch(/Sustainability|Design|Cost-effectiveness|Durability|Brand recognition/);
  });

  test("responses are ordered by question number", async ({ page }) => {
    await page.waitForLoadState("networkidle");

    const questionBadges = page.getByTestId('question-number');
    
    await expect(questionBadges.first()).toBeVisible({ timeout: 15000 });
    
    const count = await questionBadges.count();

    expect(count).toBeGreaterThan(1);
    
    const firstText = await questionBadges.nth(0).textContent();
    const secondText = await questionBadges.nth(1).textContent();

    expect(firstText).toBeTruthy();
    expect(secondText).toBeTruthy();
    
    const firstNum = parseInt(firstText!.match(/\d+/)?.[0] || "0");
    const secondNum = parseInt(secondText!.match(/\d+/)?.[0] || "0");

    expect(secondNum).toBeGreaterThanOrEqual(firstNum);
  });

  test("can add stakeholder name and persists after page refresh", async ({
    page,
  }) => {
    const timestamp = Date.now();
    const stakeholderName = `Test Stakeholder ${timestamp}`;

    const editButton = page.getByTestId('edit-button').first();
    await expect(editButton).toBeVisible();
    await editButton.click();
    await page.waitForLoadState("networkidle");

    const stakeholderInput = page
      .getByPlaceholder(/business or organisation/i)
      .or(page.locator('input[placeholder*="stakeholder"]'));

    await expect(stakeholderInput.first()).toBeVisible();

    await stakeholderInput.first().fill(stakeholderName);

    const saveButton = page
      .getByRole("button", { name: /save/i })
      .first();

    await expect(saveButton).toBeVisible();

    await saveButton.first().click();
    await page.waitForLoadState("networkidle");

    await expect(page.getByText(stakeholderName)).toBeVisible();

    await page.reload();
    await page.waitForLoadState("networkidle");

    await expect(page.getByText(stakeholderName)).toBeVisible();
  });

  test.afterAll(async () => {
    await deleteFixtureData(testData);
  });

});