import { test, expect } from "@playwright/test";
import { CleanupManager, createFixtureData } from "./helpers";
import { defaultUser, setupConsultation } from "../fixtures";
import type { FixtureReference } from "../fixtures";

// The User List and Question List groups only read the consultation dashboard,
// so they share a single fixture created once for the whole block.
test.describe("Admin Dashboard - Dashboard Page", () => {
  const cleanupManager = new CleanupManager();
  let testData: FixtureReference = {};
  let consultationId: string;

  test.beforeAll(async ({ request }) => {
    testData = await createFixtureData(request, {
      consultations: [setupConsultation],
    });
    cleanupManager.add(testData);
    consultationId = testData.consultation_ids![0];
  });

  test.beforeEach(async ({ page }) => {
    await page.goto(`/support/consultations/${consultationId}`);
    await page.waitForLoadState("networkidle");
  });

  test.describe("User List", () => {
    test("displays users table with correct column headers", async ({ page }) => {
      await expect(page.getByRole("heading", { name: "users" })).toBeVisible();
      await expect(page.getByText("email", { exact: true })).toBeVisible();
      await expect(page.getByText("created at", { exact: true })).toBeVisible();
      await expect(
        page.getByText("can access support console & dashboards", { exact: true })
      ).toBeVisible();
      await expect(page.getByText("actions", { exact: true }).first()).toBeVisible();
    });

    test("lists users assigned to the consultation", async ({ page }) => {
      await expect(page.getByText(defaultUser.email)).toBeVisible();
    });

    test("shows add users button linking to add user page", async ({ page }) => {
      const addUsersLink = page.locator(
        `a[href="/support/consultations/${consultationId}/users/new/"]`
      );
      await expect(addUsersLink).toBeVisible();
    });

    test("can navigate to user details page via email link", async ({ page }) => {
      const userLink = page.getByRole("button", { name: defaultUser.email });
      // The fixture assigns one user, so a count > 1 means a duplicate regression.
      await expect(userLink).toHaveCount(1);
      await userLink.click();
      await page.waitForLoadState("networkidle");
      await expect(page).toHaveURL(/\/support\/users\/.+/);
    });
  });

  test.describe("Question List", () => {
    test("displays questions table with correct column headers", async ({ page }) => {
      await expect(page.getByRole("heading", { name: "questions" })).toBeVisible();
      await expect(page.getByText("number", { exact: true })).toBeVisible();
      await expect(page.getByText("text", { exact: true })).toBeVisible();
      await expect(page.getByText("free text", { exact: true })).toBeVisible();
      await expect(page.getByText("multiple choice", { exact: true })).toBeVisible();
    });

    test("displays all questions for the consultation", async ({ page }) => {
      const questions = setupConsultation.questions!;

      await expect(
        page.getByRole("button", { name: /delete question .*/ }),
      ).toHaveCount(questions.length);

      // Check each question's text, not just the row count, so a mislabelled
      // or missing row is caught.
      for (const question of questions) {
        await expect(page.getByText(question.text).first()).toBeVisible();
      }
    });

    test("shows delete link for each question", async ({ page }) => {
      await expect(
        page.getByRole("button", { name: /delete question .*/ }).first()
      ).toBeVisible();
    });
  });

  test.afterAll(async () => {
    await cleanupManager.cleanup();
  });
});

test.describe("Admin Dashboard - Remove Question", () => {
  const cleanupManager = new CleanupManager();
  let testData: FixtureReference = {};
  let consultationId: string;

  // Each test gets its own fixture so the destructive delete in one test cannot
  // affect the others, regardless of execution order or parallelism.
  test.beforeEach(async ({ request, page }) => {
    testData = await createFixtureData(request, {
      consultations: [setupConsultation],
    });
    cleanupManager.add(testData);
    consultationId = testData.consultation_ids![0];

    await page.goto(`/support/consultations/${consultationId}`);
    await page.waitForLoadState("networkidle");
  });

  test("navigates to delete question confirmation page", async ({ page }) => {
    await page.getByRole("button", { name: /delete question .*/ }).first().click();
    await page.waitForLoadState("networkidle");

    await expect(page).toHaveURL(
      new RegExp(`/support/consultations/${consultationId}/questions/.+/delete`)
    );
    await expect(
      page.getByRole("heading", { name: "Delete question" })
    ).toBeVisible();
    await expect(
      page.getByText("Are you sure you want to delete the following question?")
    ).toBeVisible();
  });

  test("deletes question and redirects to consultation dashboard", async ({ page }) => {
    const deleteButtons = page.getByRole("button", { name: /delete question .*/ });
    const questionCountBefore = await deleteButtons.count();

    await deleteButtons.first().click();
    await page.waitForLoadState("networkidle");

    await page.getByRole("button", { name: "Yes, delete it" }).click();
    await page.waitForLoadState("networkidle");

    await expect(page).toHaveURL(
      new RegExp(`/support/consultations/${consultationId}$`)
    );

    // The dashboard now lists one fewer question, confirming the delete applied.
    await expect(
      page.getByRole("button", { name: /delete question .*/ })
    ).toHaveCount(questionCountBefore - 1);
  });

  test.afterEach(async () => {
    await cleanupManager.cleanup();
  });
});
