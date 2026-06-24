import { test, expect, Page } from "@playwright/test";
import {
  CleanupManager,
  createFixtureData,
} from "./helpers";
import { gotoFinaliseThemesList } from "./navigation";
import { signOffConsultation } from "../fixtures";
import type { FixtureReference } from "../fixtures";

test.describe.configure({ mode: "serial" });

const cleanupManager = new CleanupManager();

async function createTheme(page: Page, title: string, description: string) {
  const createThemeButton = page.getByRole("button", { name: "Add Custom Theme" });
  await createThemeButton.click();

  const titleInput = page.getByLabel("Theme Title");
  const descriptionInput = page.getByLabel("Theme Description");

  await titleInput.fill(title);
  await descriptionInput.fill(description);

  await page.getByRole("button", { name: "Add Theme" }).click();

  await page.waitForLoadState("networkidle");
}

function getIdFromUrl(page: Page, variant: "consultation" | "question") {
  const urlParts = page.url().split("/");
  const CONSULTATION_ID_INDEX = -3;
  const QUESTION_ID_INDEX = -1;

  return urlParts.at(variant === "consultation"
    ? CONSULTATION_ID_INDEX
    : QUESTION_ID_INDEX
  );
}

test.describe("Finalise Themes - Detail Page", () => {
  let testData: FixtureReference = {};

  test.beforeEach(async ({ page, request }) => {
    testData = await createFixtureData(request, {
      consultations: [signOffConsultation],
    });
    cleanupManager.add(testData);

    // Navigate from the consultations list into the finalise themes list page.
    await gotoFinaliseThemesList(page, signOffConsultation.title);

    // Only free-text questions have a detail page; target that card by its text
    // rather than relying on fixture order.
    const freeTextQuestion = signOffConsultation.questions!.find(
      (question) => question.has_free_text,
    )!;
    const questionCard = page
      .getByTestId("question-card")
      .filter({ hasText: freeTextQuestion.text });

    await expect(questionCard).toBeVisible();

    // Navigate to question page to find themes to finalise
    await questionCard.click();
    await page.waitForLoadState("networkidle");

    // Remove existing selected themes in case some are left
    const allRemoveButtons = await page.getByRole("button", { name: "Remove" }).all();
    for (const removeButton of allRemoveButtons) {
      await removeButton.click();
    }
    await page.waitForLoadState("networkidle");
  });

  test("Displays question details", async ({ page }) => {
    const question = signOffConsultation.questions![0];
    const questionText = `Q${question.number}: ${question.text}`;
    await expect(page.getByText(questionText, { exact: true })).toBeVisible();
    await expect(page.getByText(`${question.responses?.length} responses`)).toBeVisible();
  })

  test("Displays confirm modal with correct themes", async ({ page }) => {
    const THEME_TITLE = "Test Theme";
    const THEME_DESCRIPTION = "Test description";

    await createTheme(page, THEME_TITLE, THEME_DESCRIPTION);

    const confirmButton = page.getByRole("button", { name: "Sign Off Selected Themes (1)"});
    await confirmButton.click();

    // Selected theme is listed in confirm modal
    await expect(page.getByText("Confirm Finalising Themes")).toBeVisible();
    const confirmModalThemes = page.getByTestId("confirm-modal-theme");
    await expect(confirmModalThemes).toBeVisible();
    expect(await confirmModalThemes.first().textContent()).toContain(THEME_TITLE);

    // Clicking confirm redirects to finalising themes archive page
    await page.getByRole("button", { name: "Confirm Finalisation" }).click();
    const consultationId = getIdFromUrl(page, "consultation");
    const urlToExpect = `/consultations/${consultationId}/finalising-themes`;
    await page.waitForURL(urlToExpect);
    await expect(page).toHaveURL(urlToExpect);
  })

  test("Selecting a theme adds it to selected themes list", async ({ page }) => {
    await expect(page.getByText("No themes selected yet")).toBeVisible();
    await expect(page.getByText("0 selected")).toBeVisible();

    const selectButtons = page.getByRole("button", { name: "Select" });
    const firstSelectButton = selectButtons.first();
    await firstSelectButton.click();

    await page.waitForLoadState("networkidle");

    await expect(page.getByText("1 selected", { exact: true })).toBeVisible();
  })

  test("Creating a theme adds it to selected themes list", async ({ page }) => {
    const TEST_TITLE = "Test Theme Title";
    const TEST_DESCRIPTION = "Test Theme Description";

    await expect(page.getByText("No themes selected yet")).toBeVisible();
    await expect(page.getByText("0 selected")).toBeVisible();

    await createTheme(page, TEST_TITLE, TEST_DESCRIPTION);

    await expect(page.getByText("1 selected", { exact: true })).toBeVisible();
    await expect(page.getByRole("heading", { name: TEST_TITLE })).toBeVisible();
    await expect(page.getByText(TEST_DESCRIPTION)).toBeVisible();
    await expect(page.getByText(`Added a moment ago by ${signOffConsultation.users[0]}`)).toBeVisible();
  })

  test("Removing a theme removes it from the selected themes list", async ({ page }) => {
    await expect(page.getByText("0 selected")).toBeVisible();

    const TEST_TITLE = "Test Theme";
    const TEST_DESCRIPTION = "Test description";

    await createTheme(page, TEST_TITLE, TEST_DESCRIPTION);

    await expect(page.getByText("1 selected", { exact: true })).toBeVisible();
    await expect(page.getByText(TEST_TITLE)).toBeVisible();

    const removeThemeButton = page.getByRole("button", { name: "Remove" });
    await removeThemeButton.click();

    await expect(page.getByText("0 selected", { exact: true })).toBeVisible();
    await expect(page.getByText(TEST_TITLE)).not.toBeVisible();
  })

  test("Editing a theme updates it in the selected themes list", async ({ page }) => {
    await expect(page.getByText("0 selected")).toBeVisible();

    const TEST_TITLE = "Test Theme";
    const TEST_TITLE_UPDATED = "Updated Test Theme";
    const TEST_DESCRIPTION = "Test description";
    const TEST_DESCRIPTION_UPDATED = "Updated test description";

    await createTheme(page, TEST_TITLE, TEST_DESCRIPTION);

    await expect(page.getByText("1 selected", { exact: true })).toBeVisible();
    await expect(page.getByText(TEST_TITLE)).toBeVisible();

    const editThemeButton = page.getByRole("button", { name: "Edit" });
    await editThemeButton.click();

    const titleInput = page.getByLabel("Theme Title");
    const descriptionInput = page.getByLabel("Theme Description");

    await titleInput.fill(TEST_TITLE_UPDATED);
    await descriptionInput.fill(TEST_DESCRIPTION_UPDATED);

    await page.getByRole("button", { name: "Save Changes" }).click();

    await expect(page.getByText(TEST_TITLE_UPDATED)).toBeVisible();
    await expect(page.getByText(TEST_TITLE, { exact: true })).not.toBeVisible();
  })

  test("Clicking cancel while editing a theme does not update it", async ({ page }) => {
    await expect(page.getByText("0 selected")).toBeVisible();

    const TEST_TITLE = "Test Theme";
    const TEST_TITLE_UPDATED = "Updated Test Theme";
    const TEST_DESCRIPTION = "Test description";
    const TEST_DESCRIPTION_UPDATED = "Updated test description";

    await createTheme(page, TEST_TITLE, TEST_DESCRIPTION);

    await expect(page.getByText("1 selected", { exact: true })).toBeVisible();
    await expect(page.getByText(TEST_TITLE)).toBeVisible();

    const editThemeButton = page.getByRole("button", { name: "Edit" });
    await editThemeButton.click();

    const titleInput = page.getByLabel("Theme Title");
    const descriptionInput = page.getByLabel("Theme Description");

    await titleInput.fill(TEST_TITLE_UPDATED);
    await descriptionInput.fill(TEST_DESCRIPTION_UPDATED);

    await page.getByRole("button", { name: "Cancel" }).click();

    await expect(page.getByText(TEST_TITLE_UPDATED)).not.toBeVisible();
    await expect(page.getByText(TEST_TITLE, { exact: true })).toBeVisible();
  })

  test("Representative responses button toggles responses", async ({ page }) => {
    // initially hidden
    await expect(page.getByRole("heading", { name: "Representative Responses" })).not.toBeVisible();
    await expect(page.getByText("There are no responses")).not.toBeVisible();

    // revealed upon click
    await page.getByRole("button", { name: "Representative Responses" }).first().click();
    await expect(page.getByRole("heading", { name: "Representative Responses" })).toBeVisible();
    await expect(page.getByText("There are no responses")).toBeVisible();

    // hidden upon re-click
    await page.getByRole("button", { name: "Hide Responses" }).first().click();
    await expect(page.getByRole("heading", { name: "Representative Responses" })).not.toBeVisible();
    await expect(page.getByText("There are no responses")).not.toBeVisible();
  })

  test("Create theme panel shown/hidden accordingly", async ({ page }) => {
    // Create theme panel initially hidden
    await expect(page.getByRole("heading", { name: "Add Custom Theme" })).not.toBeVisible();

    // Clicking reveals panel
    const createThemeButton = page.getByRole("button", { name: "Add Custom Theme" });
    await createThemeButton.click();
    await expect(page.getByRole("heading", { name: "Add Custom Theme" })).toBeVisible();

    // Clicking again hides panel
    await createThemeButton.click();
    await expect(page.getByRole("heading", { name: "Add Custom Theme" })).not.toBeVisible();

    // Clicking cancel button also hides panel
    await createThemeButton.click();
    await expect(page.getByRole("heading", { name: "Add Custom Theme" })).toBeVisible();
    await page.getByRole("button", { name: "Cancel" }).click();
    await expect(page.getByRole("heading", { name: "Add Custom Theme" })).not.toBeVisible();
  })

  test("Select button disables/enables accordingly", async ({ page }) => {
    const selectButton = page.getByRole("button", { name: "Select" }).first();
    await expect(selectButton).not.toBeDisabled();

    await selectButton.click();

    await expect(page.getByRole("button", { name: "Select" }).first()).toBeDisabled();

    await page.getByRole("button", { name: "Remove" }).click();

    await expect(page.getByRole("button", { name: "Select" }).first()).not.toBeDisabled();
  })

  test("Displays correct counts", async ({ page }) => {
    // ensure at least 1 selected theme
    await createTheme(page, "test title", "test description");
    await page.getByTestId("selected-theme-card").waitFor();

    // number of select buttons correlate to number of candidate themes
    const selectButtons = page.getByRole("button", { name: "Select", exact: true });
    await expect(page.getByText(`${await selectButtons.count()} available`, { exact: true })).toBeVisible();

    // check selected theme counts
    const selectedThemeCards = page.getByTestId("selected-theme-card");
    const selectedThemeCount = await selectedThemeCards.count();
    const descriptionText = `Manage your ${selectedThemeCount} selected theme${selectedThemeCount > 1 ? "s" : ""} for AI to assign responses to. Edit titles or descriptions, or add a new theme.`;
    await expect(page.getByText(`${selectedThemeCount} selected`, { exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: `Sign Off Selected Themes (${selectedThemeCount})` })).toBeVisible();
    await expect(page.getByText(descriptionText)).toBeVisible();
  })

  test.afterEach(async () => {
    await cleanupManager.cleanup();
  });
});
