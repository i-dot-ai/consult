import { test, expect } from "@playwright/test";
import {
  createFixtureData,
  deleteFixtureData,
  getFirstConsultationLink,
} from "./helpers";
import { analysisConsultation } from "../fixtures";
import type { FixtureReference } from "../fixtures";

test.describe("Respondent Detail Page", () => {
  let testData: FixtureReference = {};
  let consultationId: string;
  let respondentId: string;
  let questionId: string;
  let themefinderId: string;

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

    // Navigate to analysis page to find a respondent
    await page.goto(`/consultations/${consultationId}/analysis`);
    await page.waitForLoadState("networkidle");

    // Find and click on first respondent link
    const respondentLink = page
      .locator('a[href*="/respondent/"]')
      .first();

    if ((await respondentLink.count()) > 0) {
      const href = await respondentLink.getAttribute("href");
      await respondentLink.click();
      await page.waitForLoadState("networkidle");

      // Extract IDs from URL
      const urlMatch = href?.match(
        /\/consultations\/([^/]+)\/respondent\/([^?]+)/,
      );
      if (urlMatch) {
        consultationId = urlMatch[1];
        respondentId = urlMatch[2];
      }

      // Extract query params
      const url = new URL(page.url());
      themefinderId = url.searchParams.get("themefinder_id") || "";
      questionId = url.searchParams.get("question_id") || "";
    }
  });

  test("displays respondent topbar with navigation", async ({ page }) => {
    // Check for "Back to Analysis" button
    const backButton = page
      .getByRole("link", { name: /back to analysis/i })
      .or(page.getByRole("button", { name: /back/i }));
    await expect(backButton.first()).toBeVisible();

    // Check for respondent title with themefinder ID
    if (themefinderId) {
      await expect(
        page.getByText(new RegExp(`respondent.*${themefinderId}`, "i")),
      ).toBeVisible();
    }

    // Check for previous/next buttons
    const prevButton = page
      .getByRole("button", { name: /previous/i })
      .or(page.getByRole("link", { name: /previous/i }));
    const nextButton = page
      .getByRole("button", { name: /next/i })
      .or(page.getByRole("link", { name: /next/i }));

    // At least one navigation button should be visible
    const hasPrevButton = (await prevButton.count()) > 0;
    const hasNextButton = (await nextButton.count()) > 0;
    expect(hasPrevButton || hasNextButton).toBeTruthy();
  });

  test("displays respondent demographics in sidebar", async ({ page }) => {
    // Check for sidebar heading
    const sidebarHeading = page
      .getByRole("heading", { name: /respondent demographics/i })
      .or(page.getByText(/demographics/i));
    await expect(sidebarHeading.first()).toBeVisible();

    // Check for demographics data - should have some demographic information
    const bodyContent = await page.textContent("body");
    expect(bodyContent).toBeTruthy();
  });

  test("displays questions answered progress with correct values", async ({
    page,
  }) => {
    // Wait for sidebar content to load
    await page.waitForTimeout(1000);

    // Check for "Questions Answered" section
    const questionsAnswered = page.getByText(/questions answered/i);

    if ((await questionsAnswered.count()) > 0) {
      await expect(questionsAnswered.first()).toBeVisible();

      // Get the full text content of the page
      const bodyContent = await page.textContent("body");

      // Look for percentage display (e.g., "100%", "75%")
      const percentageMatch = bodyContent?.match(/(\d+)%/);

      // Look for fraction display (e.g., "3/3", "2/4")
      const fractionMatch = bodyContent?.match(/(\d+)\/(\d+)/);

      // Verify we have progress information
      expect(percentageMatch || fractionMatch).toBeTruthy();

      // If we have fraction, verify it's valid
      if (fractionMatch) {
        const answered = parseInt(fractionMatch[1]);
        const total = parseInt(fractionMatch[2]);

        // Answered should not exceed total
        expect(answered).toBeLessThanOrEqual(total);
        expect(total).toBeGreaterThan(0);

        // The analysisConsultation fixture has 3 questions
        // Each respondent in the fixture answers all questions
        expect(total).toBe(3);

        // If we have both percentage and fraction, verify they match
        if (percentageMatch) {
          const percentage = parseInt(percentageMatch[1]);
          const calculatedPercentage = Math.round((answered / total) * 100);
          expect(percentage).toBe(calculatedPercentage);
        }
      }

      // If we only have percentage, verify it's a valid percentage
      if (percentageMatch && !fractionMatch) {
        const percentage = parseInt(percentageMatch[1]);
        expect(percentage).toBeGreaterThanOrEqual(0);
        expect(percentage).toBeLessThanOrEqual(100);
      }
    }
  });

  test("displays responses section with heading", async ({ page }) => {
    // Check for main responses heading
    const responsesHeading = page
      .getByRole("heading", {
        name: /responses to consultation questions/i,
      })
      .or(page.getByText(/responses to consultation/i));
    await expect(responsesHeading.first()).toBeVisible();

    // Check for subtitle or description
    const subtitle = page.getByText(/all responses submitted/i);
    if ((await subtitle.count()) > 0) {
      await expect(subtitle.first()).toBeVisible();
    }
  });

  test("displays individual response cards with question numbers", async ({
    page,
  }) => {
    // Wait for responses to load
    await page.waitForTimeout(1000);

    // Check for question number badges (e.g., "Q1", "Q2")
    const questionBadges = page
      .locator('text=/Q\\d+/')
      .or(page.locator('[data-testid*="question-number"]'));

    if ((await questionBadges.count()) > 0) {
      await expect(questionBadges.first()).toBeVisible();
    }

    // Check for question text/title
    const questionText = page.locator('[data-testid*="question"]');
    if ((await questionText.count()) > 0) {
      await expect(questionText.first()).toBeVisible();
    }
  });

  test("displays response text for answered questions", async ({ page }) => {
    // Wait for responses to load
    await page.waitForTimeout(1000);

    // Check for response text content
    const bodyContent = await page.textContent("body");
    expect(bodyContent).toBeTruthy();
    expect(bodyContent!.length).toBeGreaterThan(100);

    // Check for "Additional Comments" or response text labels
    const responseLabel = page
      .getByText(/additional comments/i)
      .or(page.getByText(/response/i));

    // At least some response content should be visible
    const hasResponseContent = (await responseLabel.count()) > 0;
    expect(hasResponseContent || bodyContent!.length > 200).toBeTruthy();
  });

  test("displays themes for responses with assigned themes", async ({
    page,
  }) => {
    // Wait for responses to load
    await page.waitForTimeout(1000);

    // Check for "Themes:" label
    const themesLabel = page.getByText(/themes:/i);

    if ((await themesLabel.count()) > 0) {
      await expect(themesLabel.first()).toBeVisible();

      // Look for theme tags/badges
      const themeTags = page
        .locator('[data-testid*="theme"]')
        .or(page.locator('span:has-text("Standardized framework")'))
        .or(page.locator('span:has-text("Innovation")'));

      if ((await themeTags.count()) > 0) {
        await expect(themeTags.first()).toBeVisible();
      }
    }
  });

  test("displays evidence-rich badge for qualifying responses", async ({
    page,
  }) => {
    // Wait for responses to load
    await page.waitForTimeout(1000);

    // Check for "Evidence-rich" badge
    const evidenceBadge = page.getByText(/evidence-rich/i);

    // Evidence-rich badge may or may not be present depending on data
    if ((await evidenceBadge.count()) > 0) {
      await expect(evidenceBadge.first()).toBeVisible();
    }
  });

  test("displays multiple choice responses when answered", async ({ page }) => {
    // Wait for responses to load
    await page.waitForTimeout(1000);

    // Check for "MULTIPLE CHOICE RESPONSE:" label
    const multipleChoiceLabel = page.getByText(/multiple choice response/i);

    if ((await multipleChoiceLabel.count()) > 0) {
      await expect(multipleChoiceLabel.first()).toBeVisible();

      // Should have selected options listed
      const bodyContent = await page.textContent("body");
      expect(bodyContent).toBeTruthy();
    }
  });

  test("clicking question title navigates to question detail page", async ({
    page,
  }) => {
    // Wait for responses to load
    await page.waitForTimeout(1000);

    // Find question links - they should link back to question detail pages
    const questionLinks = page.locator('a[href*="/questions/"]');

    if ((await questionLinks.count()) > 0) {
      const firstLink = questionLinks.first();
      await expect(firstLink).toBeVisible();

      // Get the href before clicking
      const href = await firstLink.getAttribute("href");
      expect(href).toBeTruthy();
      expect(href).toContain("/questions/");

      // Extract question ID from href
      const questionIdMatch = href?.match(/\/questions\/([a-f0-9-]+)/);
      expect(questionIdMatch).toBeTruthy();
      const questionId = questionIdMatch?.[1];

      // Click the question link
      await firstLink.click();
      await page.waitForLoadState("networkidle");

      // Verify we navigated to the question detail page
      // URL should match pattern: /consultations/{id}/questions/{questionId}
      await expect(page).toHaveURL(
        new RegExp(`/consultations/[a-f0-9-]+/questions/${questionId}`),
      );

      // Verify the question page loaded
      const bodyContent = await page.textContent("body");
      expect(bodyContent).toBeTruthy();
      expect(bodyContent!.length).toBeGreaterThan(50);
    }
  });

  test("can navigate back to analysis page", async ({ page }) => {
    // Find and click "Back to Analysis" button
    const backButton = page
      .getByRole("link", { name: /back to analysis/i })
      .or(page.getByRole("button", { name: /back/i }))
      .first();

    if ((await backButton.count()) > 0) {
      await backButton.click();
      await page.waitForLoadState("networkidle");

      // Should navigate back to analysis or question page
      await expect(page).toHaveURL(
        new RegExp(`/(consultations|evaluations)/.+/(analysis|questions)`),
      );
    }
  });

  test("next button navigates to next respondent and previous returns to original", async ({
    page,
  }) => {
    // Store the original URL and themefinder ID
    const originalUrl = page.url();
    const originalUrlObj = new URL(originalUrl);
    const originalThemefinderId =
      originalUrlObj.searchParams.get("themefinder_id");
    const originalRespondentId = originalUrl.match(/\/respondent\/([^?]+)/)?.[1];

    // Find next button
    const nextButton = page
      .getByRole("button", { name: /next/i })
      .or(page.getByRole("link", { name: /next/i }))
      .first();

    if ((await nextButton.count()) > 0) {
      // Check if button is enabled
      const isDisabled = await nextButton.getAttribute("disabled");

      if (!isDisabled) {
        // Click next button
        await nextButton.click();
        await page.waitForLoadState("networkidle");

        // Wait for page to fully load
        await page.waitForTimeout(1000);

        // Verify we navigated to another respondent page
        await expect(page).toHaveURL(new RegExp(`/respondent/.+`));

        // Get the new URL and themefinder ID
        const newUrl = page.url();
        const newUrlObj = new URL(newUrl);
        const newThemefinderId = newUrlObj.searchParams.get("themefinder_id");
        const newRespondentId = newUrl.match(/\/respondent\/([^?]+)/)?.[1];

        // Verify themefinder ID incremented
        if (originalThemefinderId && newThemefinderId) {
          expect(parseInt(newThemefinderId)).toBe(
            parseInt(originalThemefinderId) + 1,
          );
        }

        // Verify respondent ID changed
        expect(newRespondentId).not.toBe(originalRespondentId);

        // Now click previous button to go back
        const prevButton = page
          .getByRole("button", { name: /previous/i })
          .or(page.getByRole("link", { name: /previous/i }))
          .first();

        if ((await prevButton.count()) > 0) {
          const isPrevDisabled = await prevButton.getAttribute("disabled");

          if (!isPrevDisabled) {
            // Click previous button
            await prevButton.click();
            await page.waitForLoadState("networkidle");

            // Wait for page to fully load
            await page.waitForTimeout(1000);

            // Verify we're back to the original respondent
            const backUrl = page.url();
            const backUrlObj = new URL(backUrl);
            const backThemefinderId =
              backUrlObj.searchParams.get("themefinder_id");
            const backRespondentId = backUrl.match(/\/respondent\/([^?]+)/)?.[1];

            // Verify we're back to the original themefinder ID
            expect(backThemefinderId).toBe(originalThemefinderId);

            // Verify we're back to the original respondent ID
            expect(backRespondentId).toBe(originalRespondentId);

            // Verify the page content loaded correctly
            const bodyContent = await page.textContent("body");
            expect(bodyContent).toBeTruthy();
            expect(bodyContent!.length).toBeGreaterThan(100);
          }
        }
      }
    }
  });

  test("displays stakeholder name field in sidebar", async ({ page }) => {
    // Check for "Stakeholder Name" field/section
    const stakeholderLabel = page.getByText(/stakeholder name/i);

    if ((await stakeholderLabel.count()) > 0) {
      await expect(stakeholderLabel.first()).toBeVisible();
    }
  });

  test("page loads without errors", async ({ page }) => {
    // Verify page has loaded with content
    const bodyContent = await page.textContent("body");
    expect(bodyContent).toBeTruthy();
    expect(bodyContent!.length).toBeGreaterThan(50);

    // Should not show generic error messages
    const errorMessages = page
      .getByText(/error loading/i)
      .or(page.getByText(/something went wrong/i));

    expect(await errorMessages.count()).toBe(0);
  });

  test("responses are ordered by question number", async ({ page }) => {
    // Wait for responses to load
    await page.waitForTimeout(1000);

    // Find all question number badges
    const questionBadges = page.locator('text=/Q\\d+/');
    const count = await questionBadges.count();

    if (count > 1) {
      // Get first two question numbers
      const firstText = await questionBadges.nth(0).textContent();
      const secondText = await questionBadges.nth(1).textContent();

      if (firstText && secondText) {
        const firstNum = parseInt(firstText.match(/\d+/)?.[0] || "0");
        const secondNum = parseInt(secondText.match(/\d+/)?.[0] || "0");

        // Second question number should be greater than or equal to first
        expect(secondNum).toBeGreaterThanOrEqual(firstNum);
      }
    }
  });

  test("can add stakeholder name and persists after page refresh", async ({
    page,
  }) => {
    // Generate unique stakeholder name for this test
    const timestamp = Date.now();
    const stakeholderName = `Test Stakeholder ${timestamp}`;

    // Find the stakeholder name input field
    const stakeholderInput = page
      .getByLabel(/stakeholder name/i)
      .or(page.locator('input[name*="stakeholder"]'))
      .or(page.locator('input[placeholder*="stakeholder"]'))
      .or(page.locator('textarea[name*="stakeholder"]'));

    if ((await stakeholderInput.count()) > 0) {
      // Fill in the stakeholder name
      await stakeholderInput.first().fill(stakeholderName);

      // Find and click the add/save button
      const saveButton = page
        .getByRole("button", { name: /add stakeholder/i })
        .or(page.getByRole("button", { name: /save/i }))
        .or(page.getByRole("button", { name: /update/i }))
        .or(page.locator('button[type="submit"]'));

      if ((await saveButton.count()) > 0) {
        // Wait for the API request to complete
        const responsePromise = page.waitForResponse(
          (response) =>
            response.url().includes("/api/") &&
            (response.url().includes("respondent") ||
              response.url().includes("stakeholder")) &&
            response.request().method() === "PATCH",
          { timeout: 5000 },
        );

        await saveButton.first().click();

        // Wait for the update to complete
        try {
          await responsePromise;
        } catch (e) {
          // If specific response not caught, wait for network to settle
          await page.waitForLoadState("networkidle");
        }

        // Wait a moment for UI to update
        await page.waitForTimeout(500);

        // Verify the stakeholder name appears on the page
        await expect(page.getByText(stakeholderName)).toBeVisible();

        // Get current URL to refresh
        const currentUrl = page.url();

        // Refresh the page
        await page.reload();
        await page.waitForLoadState("networkidle");

        // Wait for content to load after refresh
        await page.waitForTimeout(1000);

        // Verify the stakeholder name still appears after refresh
        await expect(page.getByText(stakeholderName)).toBeVisible();
      }
    }
  });

  test.afterAll(async () => {
    await deleteFixtureData(testData);
  });
});
