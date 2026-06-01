import { test, expect, Page } from "@playwright/test";
import {
  createFixtureData,
  deleteFixtureData,
  getFirstConsultationLink,
} from "./helpers";
import { signOffConsultation } from "../fixtures";
import type { FixtureReference } from "../fixtures";

async function createTheme(page: Page, title: string, description: string) {
  const createThemeButton = page.getByRole("button", { name: "Add Custom Theme" });
  await createThemeButton.click();

  const titleInput = page.getByLabel("Theme Title");
  const descriptionInput = page.getByLabel("Theme Description");

  await titleInput.fill(title);
  await descriptionInput.fill(description);

  await page.getByRole("button", { name: "Add Theme" }).click();
}
test.describe("Finalise Themes - Detail Page", () => {
  let testData: FixtureReference = {};

  test.beforeAll(async ({ request }) => {
    testData = await createFixtureData(request, {
      consultations: [signOffConsultation],
    });
  });

  test.beforeEach(async ({ page }) => {
    // Navigate to consultations to find a consultation
    await page.goto("/consultations");
    await page.waitForLoadState("networkidle");
 
    await page.evaluate(() => localStorage.setItem("onboardingComplete-finalising-themes-archive", "true"));
    await page.evaluate(() => localStorage.setItem("onboardingComplete-finalising-themes", "true"));

    // Get the test consultation at sign off stage
    // Navigate to finalise themes page to find questions
    const finaliseThemesLink = page.getByTestId(`Finalise Themes for ${signOffConsultation.title}`);
    await finaliseThemesLink.click();
    await page.waitForLoadState("networkidle");

    // Get the first question and navigate to finalise themes detail
    await expect(page.getByTestId("question-card")).toHaveCount(3);
    const firstQuestionButton = page.getByTestId("question-card").first();

    expect(firstQuestionButton).toBeTruthy();

    // Navigate to question page to find themes to finalise
    await firstQuestionButton.click();
    await page.waitForLoadState("networkidle");
  });

  test("Selecting a theme adds it to selected themes list", async ({ page }) => {
    expect(page.getByText("No themes selected yet")).toBeVisible();
    expect(page.getByText("0 selected")).toBeVisible();

    const selectButtons = page.getByRole("button", { name: "Select" });
    const firstSelectButton = selectButtons.first();
    await firstSelectButton.click(); 
    expect(page.getByText("1 selected", { exact: true })).toBeVisible();
  })

  test("Creating a theme adds it to selected themes list", async ({ page }) => {
    const TEST_TITLE = "Test Theme Title";
    const TEST_DESCRIPTION = "Test Theme Description";

    expect(page.getByText("No themes selected yet")).toBeVisible();
    expect(page.getByText("0 selected")).toBeVisible();

    createTheme(page, TEST_TITLE, TEST_DESCRIPTION);

    expect(page.getByText("1 selected", { exact: true })).toBeVisible();
    expect(page.getByRole("heading", { name: TEST_TITLE })).toBeVisible();
    expect(page.getByText(TEST_DESCRIPTION)).toBeVisible();
    expect(page.getByText(`Added a moment ago by ${signOffConsultation.users[0]}`)).toBeVisible();
  })

  test("Removing a theme removes it from the selected themes list", async ({ page }) => {
    expect(page.getByText("0 selected")).toBeVisible();

    const TEST_TITLE = "Test Theme";
    const TEST_DESCRIPTION = "Test description";

    createTheme(page, TEST_TITLE, TEST_DESCRIPTION);

    expect(page.getByText("1 selected", { exact: true })).toBeVisible();
    expect(page.getByText(TEST_TITLE)).toBeVisible();

    const removeThemeButton = page.getByRole("button", { name: "Remove" });
    await removeThemeButton.click();

    expect(page.getByText("0 selected", { exact: true })).toBeVisible();
    expect(page.getByText(TEST_TITLE)).not.toBeVisible();
  })

  test("Editing a theme updates it in the selected themes list", async ({ page }) => {
    expect(page.getByText("0 selected")).toBeVisible();

    const TEST_TITLE = "Test Theme";
    const TEST_TITLE_UPDATED = "Updated Test Theme";
    const TEST_DESCRIPTION = "Test description";
    const TEST_DESCRIPTION_UPDATED = "Updated test description";

    createTheme(page, TEST_TITLE, TEST_DESCRIPTION);

    expect(page.getByText("1 selected", { exact: true })).toBeVisible();
    expect(page.getByText(TEST_TITLE)).toBeVisible();

    const editThemeButton = page.getByRole("button", { name: "Edit" });
    await editThemeButton.click();

    const titleInput = page.getByLabel("Theme Title");
    const descriptionInput = page.getByLabel("Theme Description");

    await titleInput.fill(TEST_TITLE_UPDATED);
    await descriptionInput.fill(TEST_DESCRIPTION_UPDATED);

    await page.getByRole("button", { name: "Save Changes" }).click();

    expect(page.getByText(TEST_TITLE_UPDATED)).toBeVisible();
    expect(page.getByText(TEST_TITLE, { exact: true })).not.toBeVisible();
  })

  test("Clicking cancel while editing a theme does not update it", async ({ page }) => {
    expect(page.getByText("0 selected")).toBeVisible();

    const TEST_TITLE = "Test Theme";
    const TEST_TITLE_UPDATED = "Updated Test Theme";
    const TEST_DESCRIPTION = "Test description";
    const TEST_DESCRIPTION_UPDATED = "Updated test description";

    createTheme(page, TEST_TITLE, TEST_DESCRIPTION);

    expect(page.getByText("1 selected", { exact: true })).toBeVisible();
    expect(page.getByText(TEST_TITLE)).toBeVisible();

    const editThemeButton = page.getByRole("button", { name: "Edit" });
    await editThemeButton.click();

    const titleInput = page.getByLabel("Theme Title");
    const descriptionInput = page.getByLabel("Theme Description");

    await titleInput.fill(TEST_TITLE_UPDATED);
    await descriptionInput.fill(TEST_DESCRIPTION_UPDATED);

    await page.getByRole("button", { name: "Cancel" }).click();

    expect(page.getByText(TEST_TITLE_UPDATED)).not.toBeVisible();
    expect(page.getByText(TEST_TITLE, { exact: true })).toBeVisible();
  })

  test("Create theme panel shown/hidden accordingly", async ({ page }) => {
    // Create theme panel initially hidden
    expect(page.getByRole("heading", { name: "Add Custom Theme" })).not.toBeVisible();

    // Clicking reveals panel
    const createThemeButton = page.getByRole("button", { name: "Add Custom Theme" });
    await createThemeButton.click();
    expect(page.getByRole("heading", { name: "Add Custom Theme" })).toBeVisible();

    // Clicking again hides panel
    await createThemeButton.click();
    expect(page.getByRole("heading", { name: "Add Custom Theme" })).not.toBeVisible();

    // Clicking cancel button also hides panel
    await createThemeButton.click();
    expect(page.getByRole("heading", { name: "Add Custom Theme" })).toBeVisible();
    await page.getByRole("button", { name: "Cancel" }).click();
    expect(page.getByRole("heading", { name: "Add Custom Theme" })).not.toBeVisible();
  })

  test.afterAll(async () => {
    await deleteFixtureData(testData);
  });
});
