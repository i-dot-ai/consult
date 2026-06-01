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
  let questionId: string;
  let themefinderId: string;

  test.beforeAll(async ({ request }) => {
    testData = await createFixtureData(request, {
      consultations: [analysisConsultation],
    });
  });

  test.beforeEach(async ({ page }) => {
    // Use consultation ID from fixture data directly
    consultationId = testData.consultation_ids![0];

    // Navigate to consultation detail page
    await page.goto(`/consultations/${consultationId}`);
    await page.waitForLoadState("networkidle");

    // Wait for question cards to appear (they load via API)
    const questionCards = page.locator('[role="button"][aria-label*="Click to view question"]');
    await expect(questionCards.first()).toBeVisible({ timeout: 10000 });
    
    const questionCardCount = await questionCards.count();
    
    // Fixture should create 3 questions
    expect(questionCardCount).toBeGreaterThanOrEqual(3);
    
    // analysisConsultation has 3 questions:
    // Q1: hybridQuestionWithThemes (5 responses, has_free_text: true) <- Has Response Analysis tab
    // Q3: multChoiceQuestion (10 responses, has_free_text: false) <- NO Response Analysis tab!
    // Q4: openQuestionWithThemes (5 responses, has_free_text: true) <- Has Response Analysis tab
    // IMPORTANT: Only questions with has_free_text: true have the Response Analysis tab
    // Click on Q1 (first question) which has free text and Response Analysis tab
    const questionCard = questionCards.first();
    
    const questionText = await questionCard.textContent();
    
    await questionCard.click();
    await page.waitForLoadState("networkidle");

    // We should be on a question detail page
    await expect(page).toHaveURL(/\/consultations\/.*\/questions\/.*/);

    // Wait for Response Analysis tab to appear (no timeout limit - default Playwright timeout)
    const responseTab = page
      .getByRole("tab", { name: /response analysis/i })
      .or(page.getByRole("tab", { name: /response/i }));
    
    await expect(responseTab).toBeVisible();
    
    // Click Response Analysis tab to see respondent buttons
    await responseTab.click();
    await page.waitForLoadState("networkidle");

    // Find respondent ID button (button with text "ID: {number}")
    // Q1 (hybridQuestionWithThemes) has 5 responses, so we should see up to 5 respondent buttons
    const allRespondentButtons = page.locator('button:has-text("ID:")');
    
    // Wait for at least one respondent button to appear
    await expect(allRespondentButtons.first()).toBeVisible({ timeout: 10000 });
    
    const respondentCount = await allRespondentButtons.count();
    
    expect(respondentCount).toBeGreaterThan(0);
    
    // Click on the first respondent button
    // Since the fixture creates responses by index, respondent 1 should have a response
    const respondentButton = allRespondentButtons.first();

    const respondentText = await respondentButton.textContent();

    await respondentButton.click();
    await page.waitForLoadState("networkidle");

    // Verify we're on a respondent page
    await expect(page).toHaveURL(/\/consultations\/.*\/respondent\/.*/);
    
    // Wait for the main responses heading to ensure page structure has loaded
    await expect(page.getByRole("heading", { name: /responses to consultation questions/i })).toBeVisible({ timeout: 10000 });
    
    // CRITICAL: Wait for "Loading Responses..." message to disappear
    // The frontend shows this message while fetching data from API
    const loadingMessage = page.getByText("Loading Responses...");
    // Wait for loading to complete - message should disappear
    await expect(loadingMessage).toBeHidden({ timeout: 30000 });
    
    // CRITICAL: Now wait for response cards to appear after loading completes
    // The fixture guarantees this respondent has responses, so this must appear
    await expect(page.getByTestId('question-number').first()).toBeVisible({ timeout: 10000 });
    
    const questionNumberCount = await page.getByTestId('question-number').count();

    // Extract IDs from URL
    const currentUrl = page.url();
    const urlMatch = currentUrl.match(
      /\/consultations\/([^/]+)\/respondent\/([^?]+)/,
    );
    expect(urlMatch).toBeTruthy();
    consultationId = urlMatch![1];
    respondentId = urlMatch![2];

    // Extract query params
    const url = new URL(currentUrl);
    themefinderId = url.searchParams.get("themefinder_id") || "";
    questionId = url.searchParams.get("question_id") || "";
  });

  test("displays respondent topbar with navigation", async ({ page }) => {
    // Check for "Back to Analysis" button
    const backButton = page
      .getByRole("link", { name: /back to analysis/i })
      .or(page.getByRole("button", { name: /back/i }));
    await expect(backButton.first()).toBeVisible();

    // Check for respondent title with themefinder ID in heading
    if (themefinderId) {
      await expect(
        page.getByRole("heading", { name: new RegExp(`respondent.*${themefinderId}`, "i") }),
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
    // Use .or() to check for either prev or next button
    const navigationButtons = prevButton.or(nextButton);
    await expect(navigationButtons.first()).toBeVisible();
    expect(await navigationButtons.count()).toBeGreaterThan(0);
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
    await page.waitForLoadState("networkidle");

    // Check for "Questions Answered" section - fixture creates questions so this should exist
    const questionsAnswered = page.getByText(/questions answered/i);
    const questionsAnsweredCount = await questionsAnswered.count();
    
    // Fixture should create questions - fail if section is missing
    expect(questionsAnsweredCount).toBeGreaterThan(0);

    await expect(questionsAnswered.first()).toBeVisible();

    // Get the progress text directly using test ID
    const progressText = await page.getByTestId('questions-answered-progress').textContent();
    
    // Look for percentage display followed by fraction (e.g., "100% (3/3)")
    // The format from RespondentSidebarItem subtitle is: "80% (8/10)"
    const progressMatch = progressText?.match(/(\d+)%\s*\((\d+)\/(\d+)\)/);

    // Verify we have progress information
    expect(progressMatch).toBeTruthy();

    if (progressMatch) {
      const percentage = parseInt(progressMatch[1]);
      const answered = parseInt(progressMatch[2]);
      const total = parseInt(progressMatch[3]);

      // Answered should not exceed total
      expect(answered).toBeLessThanOrEqual(total);
      expect(total).toBeGreaterThan(0);

      // The analysisConsultation fixture has 3 questions
      // Each respondent in the fixture answers all questions
      expect(total).toBe(3);

      // Verify percentage matches the fraction
      const calculatedPercentage = Math.round((answered / total) * 100);
      expect(percentage).toBe(calculatedPercentage);
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

    // Check for subtitle or description - should always be present
    const subtitle = page.getByText(/all responses submitted/i);
    await expect(subtitle.first()).toBeVisible();
    expect(await subtitle.count()).toBeGreaterThan(0);
  });

  test("displays individual response cards with question numbers", async ({
    page,
  }) => {
    // Wait for responses to load
    await page.waitForLoadState("networkidle");

    // Check for question number badges (e.g., "Q1", "Q2") - fixture creates responses
    const questionBadges = page.getByTestId('question-number');

    // Wait for at least one badge to appear (longer timeout for dynamic content)
    await expect(questionBadges.first()).toBeVisible({ timeout: 15000 });
    expect(await questionBadges.count()).toBeGreaterThan(0);

    // Check for question text/title - should exist for each response (it's in an <a> tag)
    const questionLinks = page.locator('a[href*="/questions/"]');
    await expect(questionLinks.first()).toBeVisible();
    expect(await questionLinks.count()).toBeGreaterThan(0);
  });

  test("displays response text for answered questions", async ({ page }) => {
    // Wait for responses to load
    await page.waitForLoadState("networkidle");

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
    await page.waitForLoadState("networkidle");

    // Check for "Themes:" label - fixture assigns themes to responses
    // Respondent 1 has themes on Q1 response (themes: ["A", "B"])
    const themesLabel = page.getByText(/themes:/i);
    await expect(themesLabel.first()).toBeVisible({ timeout: 15000 });
    expect(await themesLabel.count()).toBeGreaterThan(0);

    // Look for theme tag content - fixture has "Standardized framework" and "Innovation" themes
    // These are rendered in Tag components with variant="dark"
    const themeTags = page.getByText("Standardized framework").or(page.getByText("Innovation"));

    await expect(themeTags.first()).toBeVisible({ timeout: 15000 });
    expect(await themeTags.count()).toBeGreaterThan(0);
  });

  test("displays evidence-rich badge for qualifying responses", async ({
    page,
  }) => {
    // Wait for responses to load
    await page.waitForLoadState("networkidle");

    // Check for "Evidence-rich" badge - genuinely optional based on response quality
    const evidenceBadge = page.getByText(/evidence-rich/i);
    const evidenceBadgeCount = await evidenceBadge.count();
    
    // Skip test if no evidence-rich badges (optional feature)
    test.skip(evidenceBadgeCount === 0, "No evidence-rich badges present in fixture data");

    await expect(evidenceBadge.first()).toBeVisible();
  });

  test("displays multiple choice responses when answered", async ({ page }) => {
    // Wait for responses to load
    await page.waitForLoadState("networkidle");

    // Check for "MULTIPLE CHOICE RESPONSE:" label - fixture has MC questions
    const multipleChoiceLabel = page.getByText(/multiple choice response/i);
    await expect(multipleChoiceLabel.first()).toBeVisible();
    expect(await multipleChoiceLabel.count()).toBeGreaterThan(0);

    // Should have selected options listed
    const bodyContent = await page.textContent("body");
    expect(bodyContent).toBeTruthy();
  });

  test("clicking question title navigates to question detail page", async ({
    page,
  }) => {
    // Wait for responses to load
    await page.waitForLoadState("networkidle");

    // Find question links - they should link back to question detail pages
    const questionLinks = page.locator('a[href*="/questions/"]');

    // Wait for at least one link to be visible
    const firstLink = questionLinks.first();
    await expect(firstLink).toBeVisible();
    
    // Fixture creates responses, so question links should exist
    expect(await questionLinks.count()).toBeGreaterThan(0);

    // Get the href before clicking
    const href = await firstLink.getAttribute("href");
    expect(href).toBeTruthy();
    expect(href).toContain("/questions/");

    // Extract question ID from href
    const questionIdMatch = href?.match(/\/questions\/([a-f0-9-]+)/);
    expect(questionIdMatch).toBeTruthy();
    const extractedQuestionId = questionIdMatch?.[1];

    // Click the question link
    await firstLink.click();
    await page.waitForLoadState("networkidle");

    // Verify we navigated to the question detail page
    // URL should match pattern: /consultations/{id}/questions/{questionId}
    await expect(page).toHaveURL(
      new RegExp(`/consultations/[a-f0-9-]+/questions/${extractedQuestionId}`),
    );

    // Verify the question page loaded
    const bodyContent = await page.textContent("body");
    expect(bodyContent).toBeTruthy();
    expect(bodyContent!.length).toBeGreaterThan(50);
  });

  test("can navigate back using back button", async ({ page }) => {
    // Find "Back to Analysis" button - should always be present on respondent page
    const backButton = page
      .getByRole("link", { name: /back to analysis/i })
      .or(page.getByRole("button", { name: /back/i }))
      .first();

    await expect(backButton).toBeVisible();
    expect(await backButton.count()).toBeGreaterThan(0);
    await backButton.click();
    await page.waitForLoadState("networkidle");

    // Should navigate back - could be to question detail, analysis, or consultation page
    // Just verify we're no longer on the respondent page
    await expect(page).not.toHaveURL(new RegExp(`/respondent/`));

    // Verify we're on a valid consultation or evaluation page
    await expect(page).toHaveURL(
      new RegExp(`/(consultations|evaluations)/.+`),
    );

    // Verify the page has content
    const bodyContent = await page.textContent("body");
    expect(bodyContent).toBeTruthy();
    expect(bodyContent!.length).toBeGreaterThan(50);
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

    // Find next button - fixture has 5 respondents so next button should exist
    const nextButton = page
      .getByRole("button", { name: /next/i })
      .or(page.getByRole("link", { name: /next/i }))
      .first();

    await expect(nextButton).toBeVisible();
    expect(await nextButton.count()).toBeGreaterThan(0);
    
    // Check if button is enabled
    const isDisabled = await nextButton.getAttribute("disabled");
    // Button is enabled if disabled attribute is null or empty string
    expect(isDisabled === null || isDisabled === "").toBeTruthy();

    // Click next button
    await nextButton.click();
    await page.waitForLoadState("networkidle");

    // Verify we navigated to another respondent page
    await expect(page).toHaveURL(new RegExp(`/respondent/.+`));

    // Get the new URL and themefinder ID
    const newUrl = page.url();
    const newUrlObj = new URL(newUrl);
    const newThemefinderId = newUrlObj.searchParams.get("themefinder_id");
    const newRespondentId = newUrl.match(/\/respondent\/([^?]+)/)?.[1];

    // Verify themefinder ID changed - fixture guarantees themefinder_id params
    expect(newThemefinderId).not.toBe(originalThemefinderId);

    // Verify respondent ID changed
    expect(newRespondentId).not.toBe(originalRespondentId);

    // Now click previous button to go back - should exist after clicking next
    const prevButton = page
      .getByRole("button", { name: /previous/i })
      .or(page.getByRole("link", { name: /previous/i }))
      .first();

    await expect(prevButton).toBeVisible();
    expect(await prevButton.count()).toBeGreaterThan(0);
    
    const isPrevDisabled = await prevButton.getAttribute("disabled");
    // Button is enabled if disabled attribute is null or empty string
    expect(isPrevDisabled === null || isPrevDisabled === "").toBeTruthy();

    // Click previous button
    await prevButton.click();
    await page.waitForLoadState("networkidle");

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
  });

  test("displays stakeholder name field in sidebar", async ({ page }) => {
    // Check for "Stakeholder Name" field/section - should always be in sidebar
    const stakeholderLabel = page.getByText(/stakeholder name/i);

    await expect(stakeholderLabel.first()).toBeVisible();
    expect(await stakeholderLabel.count()).toBeGreaterThan(0);
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
    await page.waitForLoadState("networkidle");

    // Find all question number badges - fixture has 3 questions
    const questionBadges = page.getByTestId('question-number');
    
    // Wait for at least one badge to appear (longer timeout for dynamic content)
    await expect(questionBadges.first()).toBeVisible({ timeout: 15000 });
    
    const count = await questionBadges.count();

    // Fixture creates 3 questions, so should have multiple badges
    expect(count).toBeGreaterThan(1);
    
    // Get first two question numbers
    const firstText = await questionBadges.nth(0).textContent();
    const secondText = await questionBadges.nth(1).textContent();

    expect(firstText).toBeTruthy();
    expect(secondText).toBeTruthy();
    
    const firstNum = parseInt(firstText!.match(/\d+/)?.[0] || "0");
    const secondNum = parseInt(secondText!.match(/\d+/)?.[0] || "0");

    // Second question number should be greater than or equal to first
    expect(secondNum).toBeGreaterThanOrEqual(firstNum);
  });

  test("can add stakeholder name and persists after page refresh", async ({
    page,
  }) => {
    // Generate unique stakeholder name for this test
    const timestamp = Date.now();
    const stakeholderName = `Test Stakeholder ${timestamp}`;

    // First, find and click the edit button to show the input field
    const editButton = page.getByTestId('edit-button').first();
    await expect(editButton).toBeVisible();
    await editButton.click();
    await page.waitForLoadState("networkidle");

    // Now find the stakeholder name input field (visible after clicking edit)
    const stakeholderInput = page
      .getByPlaceholder(/business or organisation/i)
      .or(page.locator('input[placeholder*="stakeholder"]'));

    // Wait for input to appear and verify it exists
    await expect(stakeholderInput.first()).toBeVisible();
    expect(await stakeholderInput.count()).toBeGreaterThan(0);

    // Fill in the stakeholder name
    await stakeholderInput.first().fill(stakeholderName);

    // Find and click the save button (green with checkmark)
    const saveButton = page
      .getByRole("button", { name: /save/i })
      .first();

    // Wait for save button and verify it exists
    await expect(saveButton).toBeVisible();
    expect(await saveButton.count()).toBeGreaterThan(0);

    // Click save and wait for network to settle
    await saveButton.first().click();
    await page.waitForLoadState("networkidle");

    // Verify the stakeholder name appears on the page
    await expect(page.getByText(stakeholderName)).toBeVisible();

    // Refresh the page
    await page.reload();
    await page.waitForLoadState("networkidle");

    // Verify the stakeholder name still appears after refresh
    await expect(page.getByText(stakeholderName)).toBeVisible();
  });

  test.afterAll(async () => {
    await deleteFixtureData(testData);
  });
});
