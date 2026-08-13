import { test, expect } from "@playwright/test";
import type { Locator, Page } from "@playwright/test";
import { CleanupManager, createFixtureData } from "./helpers";
import { analysisConsultation, hybridQuestionWithThemes } from "../fixtures";
import type { FixtureReference } from "../fixtures";

// Covers the question summary page (`/consultations/{id}/questions/{qid}`).
// Uses the first question of `analysisConsultation` (the hybrid question) which
// has free text, multiple choice options and assigned themes, so every section
// of the page is exercised. The response counts asserted below are derived from
// the fixture rather than hardcoded, so they stay correct if the fixture changes.
const responses = hybridQuestionWithThemes.responses ?? [];
const TOTAL_RESPONSES = responses.length;

const responsesWithTheme = (themeKey: string) =>
  responses.filter((response) => response.themes?.includes(themeKey)).length;
const responsesWithNation = (nation: string) =>
  responses.filter((response) => response.demographics?.nation === nation)
    .length;
const responsesWithChoice = (option: string) =>
  responses.filter((response) => response.chosen_options?.includes(option))
    .length;
const responsesMatchingText = (substring: string) =>
  responses.filter((response) =>
    response.free_text?.toLowerCase().includes(substring.toLowerCase()),
  ).length;

test.describe("Question Summary Page", () => {
  const cleanupManager = new CleanupManager();
  let testData: FixtureReference = {};
  let consultationId: string;
  let questionId: string;

  // A response card renders one uniquely-keyed respondent button, so counting
  // these is a reliable proxy for the number of free-text responses shown.
  const responseCards = (page: Page): Locator =>
    page.locator('[data-testid^="respondent-button-"]');

  const filteredBadge = (page: Page): Locator => page.getByText("Filtered");
  const clearButton = (page: Page): Locator =>
    page.getByRole("button", { name: /^clear$/i });

  test.beforeAll(async ({ request }) => {
    testData = await createFixtureData(request, {
      consultations: [analysisConsultation],
    });
    cleanupManager.add(testData);
  });

  test.beforeEach(async ({ page }) => {
    consultationId = testData.consultation_ids![0];
    questionId = testData.question_ids![0];

    await page.goto(`/consultations/${consultationId}/questions/${questionId}`);
    await page.waitForLoadState("networkidle");

    // Wait for the question card (summary header) to render. The card shows
    // skeletons until the consultation and question stores resolve, so allow a
    // generous timeout to absorb load spikes when the suite runs in parallel.
    await expect(
      page.getByText(`Q${hybridQuestionWithThemes.number}:`, { exact: false }),
    ).toBeVisible();
  });

  test("displays the question text in the summary header", async ({ page }) => {
    await expect(
      page.getByText(hybridQuestionWithThemes.text).first(),
    ).toBeVisible();
  });

  test("filter sidebar shows expected demographics", async ({ page }) => {
    await expect(page.getByRole("heading", { name: /filters/i })).toBeVisible();

    const sidebar = page.getByTestId("filters-sidebar");

    // Demographic categories from the fixture: "age_group" and "nation".
    // The sidebar shows skeletons until the demographics request resolves, so
    // give this first assertion the longer timeout to wait for the real data.
    await expect(sidebar.getByText("age_group", { exact: true })).toBeVisible();
    await expect(sidebar.getByText("nation", { exact: true })).toBeVisible();

    // Demographic values from the fixture should be listed.
    for (const value of ["England", "Wales", "Scotland"]) {
      await expect(
        sidebar.getByText(value, { exact: true }).first(),
      ).toBeVisible();
    }
    for (const ageGroup of ["18-35", "36-50", "51-65"]) {
      await expect(
        sidebar.getByText(ageGroup, { exact: true }).first(),
      ).toBeVisible();
    }
  });

  test("displays multiple choice answers", async ({ page }) => {
    await expect(
      page.getByRole("heading", { name: /multiple choice answers/i }),
    ).toBeVisible();

    // Each option label is rendered as a heading within the section.
    for (const option of hybridQuestionWithThemes.multiple_choice_options ?? []) {
      await expect(
        page.getByRole("heading", { name: option, exact: true }),
      ).toBeVisible();
    }
  });

  test("displays themes in the theme analysis section", async ({ page }) => {
    await expect(
      page.getByRole("heading", { name: /theme analysis/i }),
    ).toBeVisible();

    // Theme names also appear on response cards, so scope assertions to the
    // theme analysis table rows (rendered as role="button").
    const themeRows = page.locator('tr[role="button"]');
    await expect(themeRows.first()).toBeVisible();

    for (const theme of hybridQuestionWithThemes.themes ?? []) {
      await expect(
        themeRows.filter({ hasText: theme.name }).first(),
      ).toBeVisible();
      await expect(
        themeRows.filter({ hasText: theme.description }).first(),
      ).toBeVisible();
    }
  });

  test("orders themes by number of mentions (descending)", async ({ page }) => {
    await expect(
      page.getByRole("heading", { name: /theme analysis/i }),
    ).toBeVisible();

    const themeRows = page.locator('tr[role="button"]');
    await expect(themeRows.first()).toBeVisible();

    const rowTexts = await themeRows.allTextContents();

    // The fixture lists themes in descending order of mentions, so themes[0]
    // ("Standardized framework", 3 mentions) must render before themes[1]
    // ("Innovation", 2 mentions) in the count-sorted table.
    const themes = hybridQuestionWithThemes.themes ?? [];
    const moreMentionedIndex = rowTexts.findIndex((text) =>
      text.includes(themes[0].name),
    );
    const lessMentionedIndex = rowTexts.findIndex((text) =>
      text.includes(themes[1].name),
    );

    expect(moreMentionedIndex).toBeGreaterThanOrEqual(0);
    expect(lessMentionedIndex).toBeGreaterThanOrEqual(0);
    expect(moreMentionedIndex).toBeLessThan(lessMentionedIndex);
  });

  test("renders all free text response cards", async ({ page }) => {
    await expect(
      page.getByRole("heading", { name: /free text responses/i }),
    ).toBeVisible();

    // All free-text responses fit on one page, so every card renders.
    await expect(responseCards(page)).toHaveCount(TOTAL_RESPONSES);
    await expect(
      page.getByText(new RegExp(`showing all ${TOTAL_RESPONSES} responses`, "i")),
    ).toBeVisible();

    // The free-text filter toggles should be available.
    await expect(page.getByText("Evidence rich", { exact: true })).toBeVisible();
    await expect(page.getByText("Unread", { exact: true })).toBeVisible();
    await expect(page.getByText("Flagged", { exact: true })).toBeVisible();
  });

  test("filtering by a theme narrows the responses and can be cleared", async ({
    page,
  }) => {
    await expect(responseCards(page)).toHaveCount(TOTAL_RESPONSES);

    // Filter by the top theme; the fixture assigns it to a known subset.
    const topTheme = hybridQuestionWithThemes.themes![0];
    await page
      .locator('tr[role="button"]')
      .filter({ hasText: topTheme.name })
      .first()
      .click();

    await expect(filteredBadge(page)).toBeVisible();
    await expect(responseCards(page)).toHaveCount(
      responsesWithTheme(topTheme.key),
    );

    // Clearing the filter restores the full list.
    await clearButton(page).click();
    await expect(filteredBadge(page)).toBeHidden();
    await expect(responseCards(page)).toHaveCount(TOTAL_RESPONSES);
  });

  test("filtering by a demographic narrows the responses and can be cleared", async ({
    page,
  }) => {
    await expect(responseCards(page)).toHaveCount(TOTAL_RESPONSES);

    // Filter by a nation present in the fixture's respondent demographics.
    const nation = "England";
    const sidebar = page.getByTestId("filters-sidebar");
    await sidebar.getByText(nation, { exact: true }).first().click();

    await expect(filteredBadge(page)).toBeVisible();
    await expect(responseCards(page)).toHaveCount(responsesWithNation(nation));

    await clearButton(page).click();
    await expect(filteredBadge(page)).toBeHidden();
    await expect(responseCards(page)).toHaveCount(TOTAL_RESPONSES);
  });

  test("filtering by a multiple choice answer narrows the responses and can be cleared", async ({
    page,
  }) => {
    await expect(responseCards(page)).toHaveCount(TOTAL_RESPONSES);

    // Each multiple choice option label is rendered as a heading, which is
    // unique on the page (response card answer tags are plain spans).
    const choice = "No";
    await page.getByRole("heading", { name: choice, exact: true }).click();

    await expect(filteredBadge(page)).toBeVisible();
    await expect(responseCards(page)).toHaveCount(responsesWithChoice(choice));

    await clearButton(page).click();
    await expect(filteredBadge(page)).toBeHidden();
    await expect(responseCards(page)).toHaveCount(TOTAL_RESPONSES);
  });

  test("searching responses narrows the list and can be cleared", async ({
    page,
  }) => {
    await expect(responseCards(page)).toHaveCount(TOTAL_RESPONSES);

    // "disagree" appears in exactly one response's free text.
    const searchTerm = "disagree";
    await page.getByTestId("responses-search-input").fill(searchTerm);

    await expect(filteredBadge(page)).toBeVisible();
    await expect(responseCards(page)).toHaveCount(responsesMatchingText(searchTerm));

    await clearButton(page).click();
    await expect(filteredBadge(page)).toBeHidden();
    await expect(responseCards(page)).toHaveCount(TOTAL_RESPONSES);
  });

  test("back button returns to the consultation detail page", async ({
    page,
  }) => {
    const backButton = page.getByTestId("back-to-all-questions-button");
    await expect(backButton).toBeVisible();

    await backButton.click();
    await page.waitForLoadState("networkidle");

    await expect(page).toHaveURL(
      new RegExp(`/consultations/${consultationId}/?$`),
    );
  });

  test.afterAll(async () => {
    await cleanupManager.cleanup();
  });
});
