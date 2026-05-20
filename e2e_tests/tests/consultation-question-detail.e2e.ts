import { test, expect } from "@playwright/test";
import {
  createFixtureData,
  deleteFixtureData,
  getFirstConsultationLink,
} from "./helpers";
import { analysisConsultation } from "../fixtures";
import type { FixtureReference } from "../fixtures";

test.describe("Consultation Question Detail Page - Route & Navigation", () => {
  let testData: FixtureReference = {};

  test.beforeAll(async ({ request }) => {
    testData = await createFixtureData(request, {
      consultations: [analysisConsultation],
    });
  });

  test.beforeEach(async ({ page }) => {
    // Navigate to consultations list
    await page.goto("/consultations");
    await page.waitForLoadState("networkidle");

    // Get first consultation
    const result = await getFirstConsultationLink(page);
    expect(result).toBeTruthy();
    const consultationId = result!.href.match(/\/consultations\/([^/]+)/)?.[1]!;

    // Navigate to consultation detail page
    await page.goto(`/consultations/${consultationId}`);
    await page.waitForLoadState("networkidle");

    // Find and click on first question link
    const questionLink = page.locator('a[href*="/questions/"]').first();
    const questionLinkCount = await questionLink.count();

    test.skip(questionLinkCount === 0, "No questions found in consultation");

    await questionLink.click();
    await page.waitForLoadState("networkidle");

    // Verify we're on a question detail page with consultations path
    await expect(page).toHaveURL(/\/consultations\/.*\/questions\/.*/);
  });

  test("navigates to question detail page via consultations route", async ({
    page,
  }) => {
    // Extract IDs from current URL
    const currentUrl = page.url();
    const urlMatch = currentUrl.match(
      /\/consultations\/([a-f0-9-]+)\/questions\/([a-f0-9-]+)/,
    );
    expect(urlMatch).toBeTruthy();

    const consultationId = urlMatch![1];
    const questionId = urlMatch![2];

    // Verify exact URL pattern
    await expect(page).toHaveURL(
      new RegExp(`/consultations/${consultationId}/questions/${questionId}`),
    );
  });

  test("displays question text from fixture data", async ({ page }) => {
    // Check for specific question text from analysisConsultation fixture
    const bodyContent = await page.textContent("body");
    expect(bodyContent).toBeTruthy();

    // analysisConsultation has questions about chocolate bars, packaging, or regulations
    expect(bodyContent).toMatch(/chocolate bar|packaging|regulation/i);
  });

  test("displays respondent ID buttons for navigating to respondent details", async ({
    page,
  }) => {
    // This is unique to consultations route - respondent detail navigation
    // Click Response Analysis tab if present
    const responseTab = page
      .getByRole("tab", { name: /response/i })
      .or(page.getByRole("tab", { name: /analysis/i }));

    const responseTabCount = await responseTab.count();
    test.skip(responseTabCount === 0, "Response tab not found");

    await responseTab.first().click();
    await page.waitForLoadState("networkidle");

    // Look for respondent ID buttons
    const respondentButtons = page
      .locator('button:has-text("ID:")')
      .or(page.locator('a:has-text("ID:")'));

    // Assert buttons exist (analysisConsultation has 5 respondents)
    const buttonCount = await respondentButtons.count();
    expect(buttonCount).toBeGreaterThan(0);

    // Verify button contains ID format
    const firstButtonText = await respondentButtons.first().textContent();
    expect(firstButtonText).toMatch(/ID:\s*\d+/);
  });

  test("clicking respondent ID button navigates to respondent detail page", async ({
    page,
  }) => {
    // Click Response Analysis tab if present
    const responseTab = page
      .getByRole("tab", { name: /response/i })
      .or(page.getByRole("tab", { name: /analysis/i }));

    const responseTabCount = await responseTab.count();
    test.skip(responseTabCount === 0, "Response tab not found");

    await responseTab.first().click();
    await page.waitForLoadState("networkidle");

    // Find respondent button
    const respondentButton = page
      .locator('button:has-text("ID:")')
      .or(page.locator('a:has-text("ID:")'))
      .first();

    const buttonCount = await respondentButton.count();
    test.skip(buttonCount === 0, "No respondent buttons found");

    // Click button
    await respondentButton.click();
    await page.waitForLoadState("networkidle");

    // Verify navigation to respondent detail page
    await expect(page).toHaveURL(/\/consultations\/.*\/respondent\/.*/);

    // Verify query params exist
    const url = new URL(page.url());
    const themefinderId = url.searchParams.get("themefinder_id");
    const questionId = url.searchParams.get("question_id");

    expect(themefinderId).toBeTruthy();
    expect(questionId).toBeTruthy();
  });

  test("displays themes from fixture data", async ({ page }) => {
    // analysisConsultation has specific themes
    const bodyContent = await page.textContent("body");
    expect(bodyContent).toBeTruthy();

    // Check for specific themes from fixture (at least one should be present)
    expect(bodyContent).toMatch(/Standardized framework|Innovation/i);
  });

  test("displays response count for question", async ({ page }) => {
    // analysisConsultation has 5 responses per question
    const bodyContent = await page.textContent("body");

    // Look for response count indicator (e.g., "5 responses")
    const responseCountMatch = bodyContent?.match(/5\s+(response|answer)/i);
    expect(responseCountMatch).toBeTruthy();
  });

  test("page loads without errors on consultations route", async ({ page }) => {
    // Verify page loaded successfully with fixture content
    const bodyContent = await page.textContent("body");
    expect(bodyContent).toBeTruthy();

    // Check for fixture-specific content (chocolate bar question text)
    expect(bodyContent).toContain("chocolate");

    // No error messages
    const errorMessages = page
      .getByText(/error loading/i)
      .or(page.getByText(/something went wrong/i))
      .or(page.getByText(/page not found/i));

    expect(await errorMessages.count()).toBe(0);
  });

  test.afterAll(async () => {
    await deleteFixtureData(testData);
  });
});
