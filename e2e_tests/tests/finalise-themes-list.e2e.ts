import { test, expect } from "@playwright/test";
import {
  CleanupManager,
  createFixtureData,
} from "./helpers";
import { gotoFinaliseThemesList } from "./navigation";
import { signOffConsultation } from "../fixtures";
import type { FixtureReference } from "../fixtures";

// Shared fixture data is created once in beforeAll; serial mode prevents
// fullyParallel from running tests across workers and racing over it
test.describe.configure({ mode: "serial" });

const cleanupManager = new CleanupManager();

// Questions with free text are signed off in the finalise themes flow;
// multiple-choice-only questions are not. Derived from the fixture so it
// stays correct if the fixture's questions change.
const FREE_TEXT_QUESTION_COUNT = (signOffConsultation.questions ?? []).filter(
  (question) => question.has_free_text,
).length;

test.describe("Finalise Themes - List Page", () => {
  let testData: FixtureReference = {};

  test.beforeAll(async ({ request }) => {
    testData = await createFixtureData(request, {
      consultations: [signOffConsultation],
    });
    cleanupManager.add(testData);
  });

  test("Get started help box displays and can be dismissed", async ({
    page,
  }) => {
    // Keep the onboarding tour visible (every other test dismisses it).
    await gotoFinaliseThemesList(page, signOffConsultation.title, { dismissOnboarding: false });

    await expect(
      page.getByRole("heading", { name: "Welcome to Finalise Themes" }),
    ).toBeVisible();
    await expect(
      page.getByText("3-step process to finalise themes"),
    ).toBeVisible();

    await page.getByRole("button", { name: "Get Started" }).click();
    await expect(
      page.getByRole("heading", { name: "Welcome to Finalise Themes" }),
    ).not.toBeVisible();
  });

  test("Process panel shows the correct stage", async ({ page }) => {
    await gotoFinaliseThemesList(page, signOffConsultation.title);

    await expect(
      page.getByRole("heading", { name: "Finalising Themes" }).first(),
    ).toBeVisible();

    await expect(
      page.getByText(
        `0 of ${FREE_TEXT_QUESTION_COUNT} questions signed off`,
      ),
    ).toBeVisible();

    // Later steps in the 4-step progress bar render even at this stage.
    await expect(
      page.getByText("Assigning Themes (AI)"),
    ).toBeVisible();
  });

  test("Number of questions is correct", async ({ page }) => {
    await gotoFinaliseThemesList(page, signOffConsultation.title);

    const questionCount = signOffConsultation.questions!.length;
    await expect(
      page.getByText(`${questionCount} questions`, { exact: true }),
    ).toBeVisible();
  });

  test("Question list displays all questions", async ({ page }) => {
    await gotoFinaliseThemesList(page, signOffConsultation.title);

    const questions = signOffConsultation.questions!;
    await expect(page.getByTestId("question-card")).toHaveCount(questions.length);

    for (const question of questions) {
      await expect(page.getByText(question.text).first()).toBeVisible();
    }
  });

  test("Searching filters the question list", async ({ page }) => {
    await gotoFinaliseThemesList(page, signOffConsultation.title);

    // The open question (free text, no multiple choice) is the only one whose
    // opening words are unique, so search for those rather than a hardcoded
    // string or a positional index into the fixture.
    const openQuestion = signOffConsultation.questions!.find(
      (question) => question.has_free_text && !question.has_multiple_choice,
    )!;
    const searchTerm = openQuestion.text.split(" ").slice(0, 4).join(" ");
    await page.locator("#search-input").fill(searchTerm);

    await expect(page.getByTestId("question-card")).toHaveCount(1);
    await expect(page.getByText(openQuestion.text).first()).toBeVisible();

    // A search with no matches shows the empty state.
    await page.locator("#search-input").fill("no question matches this");
    await expect(
      page.getByText("No questions found matching your search."),
    ).toBeVisible();
  });

  test("Question status tags are shown", async ({ page }) => {
    await gotoFinaliseThemesList(page, signOffConsultation.title);

    // The multiple choice question is tagged accordingly. Use exact match:
    // the card subtext also mentions "Multiple choice data".
    await expect(
      page.getByText("Multiple choice", { exact: true }),
    ).toBeVisible();

    // No question has been signed off yet. Exact match targets the card tag,
    // not the stage panel prose which also contains "sign off".
    await expect(
      page.getByText("Signed off", { exact: true }),
    ).not.toBeVisible();
  });

  test("Favouriting a question persists across reload", async ({ page }) => {
    await gotoFinaliseThemesList(page, signOffConsultation.title);

    const favButton = page.getByTestId(/^favourite-button-/).first();
    await expect(favButton).toBeVisible();

    const testId = await favButton.getAttribute("data-testid");
    expect(testId).toBeTruthy();

    await expect(favButton).toHaveAttribute("aria-pressed", "false");

    await favButton.click();
    await expect(favButton).toHaveAttribute("aria-pressed", "true");

    await page.reload();
    await page.waitForLoadState("networkidle");
    // Cards re-render client-side after reload; wait before checking state.
    await expect(page.getByTestId("question-card").first()).toBeVisible();

    const favButtonAfterReload = page.getByTestId(testId!);
    await expect(favButtonAfterReload).toHaveAttribute("aria-pressed", "true");
  });

  test("Clicking a question navigates to its detail page", async ({ page }) => {
    await gotoFinaliseThemesList(page, signOffConsultation.title);

    const consultationId = page
      .url()
      .match(/\/consultations\/([^/]+)\/finalising-themes/)?.[1];
    expect(consultationId).toBeTruthy();

    // Only free-text questions have a detail page to navigate to.
    const freeTextQuestion = signOffConsultation.questions!.find(
      (question) => question.has_free_text,
    )!;
    await page
      .getByTestId("question-card")
      .filter({ hasText: freeTextQuestion.text })
      .click();
    await page.waitForLoadState("networkidle");

    await expect(page).toHaveURL(
      new RegExp(`/consultations/${consultationId}/finalising-themes/[^/]+$`),
    );
  });

  test.afterAll(async () => {
    await cleanupManager.cleanup();
  });
});
