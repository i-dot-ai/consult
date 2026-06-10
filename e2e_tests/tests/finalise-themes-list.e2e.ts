import { test, expect, Page } from "@playwright/test";
import {
  createFixtureData,
  deleteFixtureData,
} from "./helpers";
import { signOffConsultation } from "../fixtures";
import type { FixtureReference } from "../fixtures";

// Shared fixture data is created once in beforeAll; serial mode prevents
// fullyParallel from running tests across workers and racing over it
test.describe.configure({ mode: "serial" });

const ONBOARDING_KEY = "onboardingComplete-finalising-themes-archive";

// Number of questions with free text responses in signOffConsultation
// (hybrid Q1 + open Q4; the multiple choice Q3 has no free text).
const FREE_TEXT_QUESTION_COUNT = 2;

/**
 * Navigates from the consultations list to the finalise themes list page.
 * By default the onboarding tour is dismissed so it does not overlay the page.
 */
async function gotoListPage(
  page: Page,
  { dismissOnboarding = true }: { dismissOnboarding?: boolean } = {},
) {
  await page.goto("/consultations");
  await page.waitForLoadState("networkidle");

  if (dismissOnboarding) {
    await page.evaluate(
      (key) => localStorage.setItem(key, "true"),
      ONBOARDING_KEY,
    );
  }

  const finaliseThemesLink = page.getByTestId(
    `Finalise Themes for ${signOffConsultation.title}`,
  );
  await finaliseThemesLink.first().click();
  await page.waitForLoadState("networkidle");

  // The page is rendered with client:only, so questions are fetched after
  // hydration. Wait for the cards to render before asserting on the
  // client-rendered content (count, stage panel, tags, etc.).
  await expect(page.getByTestId("question-card").first()).toBeVisible();
}

test.describe("Finalise Themes - List Page", () => {
  let testData: FixtureReference = {};

  test.beforeAll(async ({ request }) => {
    testData = await createFixtureData(request, {
      consultations: [signOffConsultation],
    });
  });

  test("Get started help box displays and can be dismissed", async ({
    page,
  }) => {
    // Keep the onboarding tour visible (every other test dismisses it).
    await gotoListPage(page, { dismissOnboarding: false });

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
    await gotoListPage(page);

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
    await gotoListPage(page);

    const questionCount = signOffConsultation.questions!.length;
    await expect(page.getByText(`${questionCount} questions`)).toBeVisible();
  });

  test("Question list displays all questions", async ({ page }) => {
    await gotoListPage(page);

    const questionCount = signOffConsultation.questions!.length;
    await expect(page.getByTestId("question-card")).toHaveCount(questionCount);

    const freeTextQuestion = signOffConsultation.questions![0];
    await expect(
      page.getByText(freeTextQuestion.text).first(),
    ).toBeVisible();
  });

  test("Searching filters the question list", async ({ page }) => {
    await gotoListPage(page);

    // "consumer needs" is unique to the open question (Q4).
    await page.locator("#search-input").fill("consumer needs");

    await expect(page.getByTestId("question-card")).toHaveCount(1);
    await expect(
      page.getByText(signOffConsultation.questions![2].text).first(),
    ).toBeVisible();

    // A search with no matches shows the empty state.
    await page.locator("#search-input").fill("no question matches this");
    await expect(
      page.getByText("No questions found matching your search."),
    ).toBeVisible();
  });

  test("Question status tags are shown", async ({ page }) => {
    await gotoListPage(page);

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
    await gotoListPage(page);

    const favButton = page
      .locator('[data-testid^="favourite-button-"]')
      .first();
    await expect(favButton).toBeVisible();

    const testId = await favButton.getAttribute("data-testid");
    expect(testId).toBeTruthy();

    // The button's aria-label reflects favourite state.
    await expect(favButton).toHaveAttribute(
      "aria-label",
      "Add question to favourites",
    );

    await favButton.click();
    await expect(favButton).toHaveAttribute(
      "aria-label",
      "Remove question from favourites",
    );

    await page.reload();
    await page.waitForLoadState("networkidle");
    // Cards re-render client-side after reload; wait before checking state.
    await expect(page.getByTestId("question-card").first()).toBeVisible();

    const favButtonAfterReload = page.locator(`[data-testid="${testId}"]`);
    await expect(favButtonAfterReload).toHaveAttribute(
      "aria-label",
      "Remove question from favourites",
    );
  });

  test("Clicking a question navigates to its detail page", async ({ page }) => {
    await gotoListPage(page);

    const consultationId = page
      .url()
      .match(/\/consultations\/([^/]+)\/finalising-themes/)?.[1];
    expect(consultationId).toBeTruthy();

    // The first card is the free-text question, so it is clickable.
    await page.getByTestId("question-card").first().click();
    await page.waitForLoadState("networkidle");

    await expect(page).toHaveURL(
      new RegExp(`/consultations/${consultationId}/finalising-themes/[^/]+$`),
    );
  });

  test.afterAll(async () => {
    await deleteFixtureData(testData);
  });
});
