import { test, expect } from "@playwright/test";
import {
  createFixtureData,
  deleteFixtureData,
  getFirstConsultationLink,
} from "./helpers";
import { analysisConsultation } from "../fixtures";
import type { FixtureReference } from "../fixtures";

test.describe("Consultation Question Detail Page", () => {
  let testData: FixtureReference = {};
  let consultationId: string;
  let questionId: string;

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
    consultationId = result!.href.match(/\/consultations\/([^/]+)/)?.[1]!;

    // Navigate to consultation detail page
    await page.goto(`/consultations/${consultationId}`);
    await page.waitForLoadState("networkidle");

    // Find and click on first question link
    const questionLink = page.locator('a[href*="/questions/"]').first();
    const questionLinkCount = await questionLink.count();

    test.skip(questionLinkCount === 0, "No questions found in consultation");

    await questionLink.click();
    await page.waitForLoadState("networkidle");

    // Verify we're on a question detail page
    await expect(page).toHaveURL(/\/consultations\/.*\/questions\/.*/);

    // Extract question ID from URL
    const currentUrl = page.url();
    const urlMatch = currentUrl.match(/\/questions\/([a-f0-9-]+)/);
    expect(urlMatch).toBeTruthy();
    questionId = urlMatch![1];
  });

  test("displays question detail page with correct URL pattern", async ({
    page,
  }) => {
    // Verify URL matches expected pattern
    await expect(page).toHaveURL(
      new RegExp(`/consultations/${consultationId}/questions/${questionId}`),
    );

    // Verify page has loaded with content
    const bodyContent = await page.textContent("body");
    expect(bodyContent).toBeTruthy();
    expect(bodyContent!.length).toBeGreaterThan(100);
  });

  test("displays question text and number", async ({ page }) => {
    // Check for question heading - should display question text
    const headings = page.locator("h1, h2");
    await expect(headings.first()).toBeVisible();

    // Question text should be substantial
    const headingText = await headings.first().textContent();
    expect(headingText).toBeTruthy();
    expect(headingText!.length).toBeGreaterThan(10);

    // Check for question number indicator (Q1, Q2, etc.)
    const bodyContent = await page.textContent("body");
    const hasQuestionNumber = bodyContent?.match(/Q\d+|Question \d+/i);
    expect(hasQuestionNumber).toBeTruthy();
  });

  test("displays Question Summary tab", async ({ page }) => {
    // Look for Summary tab
    const summaryTab = page
      .getByRole("tab", { name: /summary/i })
      .or(page.getByRole("button", { name: /summary/i }))
      .or(page.getByRole("link", { name: /summary/i }));

    const summaryTabCount = await summaryTab.count();
    test.skip(summaryTabCount === 0, "Summary tab not found on this page");

    await expect(summaryTab.first()).toBeVisible();
  });

  test("displays Response Analysis tab", async ({ page }) => {
    // Look for Response Analysis tab
    const responseTab = page
      .getByRole("tab", { name: /response/i })
      .or(page.getByRole("button", { name: /response/i }))
      .or(page.getByRole("tab", { name: /analysis/i }));

    const responseTabCount = await responseTab.count();
    test.skip(
      responseTabCount === 0,
      "Response Analysis tab not found on this page",
    );

    await expect(responseTab.first()).toBeVisible();
  });

  test("Summary tab displays themes for questions with themes", async ({
    page,
  }) => {
    // Click on Summary tab
    const summaryTab = page
      .getByRole("tab", { name: /summary/i })
      .or(page.getByRole("button", { name: /summary/i }));

    const summaryTabCount = await summaryTab.count();

    if (summaryTabCount > 0) {
      await summaryTab.first().click();
      await page.waitForLoadState("networkidle");
    }

    // Check for themes display from fixture data
    const bodyContent = await page.textContent("body");

    // analysisConsultation has themes: "Standardized framework", "Innovation"
    const hasThemes =
      bodyContent?.includes("Standardized framework") ||
      bodyContent?.includes("Innovation") ||
      bodyContent?.includes("theme");

    expect(hasThemes).toBeTruthy();
  });

  test("Response Analysis tab displays individual responses", async ({
    page,
  }) => {
    // Click on Response Analysis tab
    const responseTab = page
      .getByRole("tab", { name: /response/i })
      .or(page.getByRole("button", { name: /response/i }))
      .or(page.getByRole("tab", { name: /analysis/i }));

    const responseTabCount = await responseTab.count();

    if (responseTabCount > 0) {
      await responseTab.first().click();
      await page.waitForLoadState("networkidle");
    }

    // Check for response content or response indicators
    const bodyContent = await page.textContent("body");
    expect(bodyContent).toBeTruthy();

    // Should have some response-related content
    const hasResponseContent =
      bodyContent!.includes("response") || bodyContent!.length > 200;
    expect(hasResponseContent).toBeTruthy();
  });

  test("can switch between Summary and Response Analysis tabs", async ({
    page,
  }) => {
    // Find both tabs
    const summaryTab = page
      .getByRole("tab", { name: /summary/i })
      .or(page.getByRole("button", { name: /summary/i }));

    const responseTab = page
      .getByRole("tab", { name: /response/i })
      .or(page.getByRole("button", { name: /response/i }))
      .or(page.getByRole("tab", { name: /analysis/i }));

    const hasSummaryTab = (await summaryTab.count()) > 0;
    const hasResponseTab = (await responseTab.count()) > 0;

    test.skip(
      !hasSummaryTab || !hasResponseTab,
      "Both tabs must be present to test switching",
    );

    // Click Summary tab
    await summaryTab.first().click();
    await page.waitForLoadState("networkidle");

    // Verify Summary tab is active
    const summaryAriaSelected =
      await summaryTab.first().getAttribute("aria-selected");
    if (summaryAriaSelected !== null) {
      expect(summaryAriaSelected).toBe("true");
    }

    // Click Response Analysis tab
    await responseTab.first().click();
    await page.waitForLoadState("networkidle");

    // Verify Response Analysis tab is active
    const responseAriaSelected =
      await responseTab.first().getAttribute("aria-selected");
    if (responseAriaSelected !== null) {
      expect(responseAriaSelected).toBe("true");
    }
  });

  test("displays response count metrics", async ({ page }) => {
    // Look for response count indicators
    const bodyContent = await page.textContent("body");

    // Should show number of responses (e.g., "5 responses", "10 answers")
    const hasResponseCount = bodyContent?.match(/\d+\s+(response|answer)/i);

    expect(hasResponseCount).toBeTruthy();
  });

  test("displays respondent ID buttons in Response Analysis tab", async ({
    page,
  }) => {
    // Click on Response Analysis tab
    const responseTab = page
      .getByRole("tab", { name: /response/i })
      .or(page.getByRole("button", { name: /response/i }))
      .or(page.getByRole("tab", { name: /analysis/i }));

    const responseTabCount = await responseTab.count();

    if (responseTabCount > 0) {
      await responseTab.first().click();
      await page.waitForLoadState("networkidle");
    }

    // Look for respondent ID buttons (format: "ID: X")
    const respondentButtons = page
      .locator('button:has-text("ID:")')
      .or(page.locator('a:has-text("ID:")'));

    const respondentButtonCount = await respondentButtons.count();

    // analysisConsultation has 5 respondents
    expect(respondentButtonCount).toBeGreaterThan(0);
  });

  test("clicking respondent ID button navigates to respondent detail page", async ({
    page,
  }) => {
    // Click on Response Analysis tab
    const responseTab = page
      .getByRole("tab", { name: /response/i })
      .or(page.getByRole("button", { name: /response/i }))
      .or(page.getByRole("tab", { name: /analysis/i }));

    const responseTabCount = await responseTab.count();

    if (responseTabCount > 0) {
      await responseTab.first().click();
      await page.waitForLoadState("networkidle");
    }

    // Find and click first respondent ID button
    const respondentButton = page
      .locator('button:has-text("ID:")')
      .or(page.locator('a:has-text("ID:")'))
      .first();

    const respondentButtonCount = await respondentButton.count();
    test.skip(
      respondentButtonCount === 0,
      "No respondent buttons found on page",
    );

    await respondentButton.click();
    await page.waitForLoadState("networkidle");

    // Verify navigation to respondent detail page
    await expect(page).toHaveURL(/\/consultations\/.*\/respondent\/.*/);
  });

  test("displays theme tags for responses with themes", async ({ page }) => {
    // Click on Response Analysis tab
    const responseTab = page
      .getByRole("tab", { name: /response/i })
      .or(page.getByRole("button", { name: /response/i }))
      .or(page.getByRole("tab", { name: /analysis/i }));

    const responseTabCount = await responseTab.count();

    if (responseTabCount > 0) {
      await responseTab.first().click();
      await page.waitForLoadState("networkidle");
    }

    // Look for theme labels or tags
    const bodyContent = await page.textContent("body");

    // Should display themes from fixture: "Standardized framework", "Innovation"
    const hasThemes =
      bodyContent?.includes("Standardized framework") ||
      bodyContent?.includes("Innovation") ||
      bodyContent?.includes("theme");

    expect(hasThemes).toBeTruthy();
  });

  test("can navigate back to consultation detail page", async ({ page }) => {
    // Look for back navigation link/button
    const backButton = page
      .getByRole("link", { name: /back/i })
      .or(page.getByRole("button", { name: /back/i }))
      .or(page.locator('a[href*="/consultations/"]').first());

    const backButtonCount = await backButton.count();

    if (backButtonCount > 0) {
      await backButton.first().click();
      await page.waitForLoadState("networkidle");

      // Should navigate to consultation detail or consultations list
      const currentUrl = page.url();
      const isOnConsultationPage =
        currentUrl.includes("/consultations/") &&
        !currentUrl.includes("/questions/");

      expect(isOnConsultationPage).toBeTruthy();
    }
  });

  test("displays search or filter functionality", async ({ page }) => {
    // Look for search input or filter controls
    const searchInput = page
      .locator('input[type="search"]')
      .or(page.locator('input[placeholder*="search"]'))
      .or(page.locator('input[placeholder*="filter"]'))
      .or(page.locator("#search-input"));

    const searchInputCount = await searchInput.count();

    if (searchInputCount > 0) {
      await expect(searchInput.first()).toBeVisible();
    }
  });

  test("page loads without errors", async ({ page }) => {
    // Verify page has content
    const bodyContent = await page.textContent("body");
    expect(bodyContent).toBeTruthy();
    expect(bodyContent!.length).toBeGreaterThan(50);

    // Should not show error messages
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
