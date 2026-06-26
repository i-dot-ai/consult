import { test, expect } from "@playwright/test";
import { CleanupManager, createFixtureData } from "./helpers";
import { defaultUser, setupConsultation, analysisConsultation } from "../fixtures";
import type { FixtureReference } from "../fixtures";

// The User List and Question List groups only read the consultation dashboard,
// so they share a single fixture created once for the whole block.
test.describe("Admin Dashboard - Dashboard Page", () => {
  const cleanupManager = new CleanupManager();
  let testData: FixtureReference = {};

  test.beforeAll(async ({ request }) => {
    testData = await createFixtureData(request, {
      consultations: [setupConsultation, analysisConsultation],
    });
    cleanupManager.add(testData);
  });

  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");
    await page.goto("/admin");
    await page.waitForLoadState("networkidle");
  });


  test("navigate to consultation list and assert count", async ({ page }) => {
    await page.locator('#consultations-consultation').getByRole('link', { name: 'Consultations' }).click();
    await page.waitForLoadState("networkidle");
    await expect(page).toHaveURL(/\/admin\/consultations\/consultation/);
    const testConsultations = await page.getByRole('link', { name: 'Test Consultation' }).count();
    expect(testConsultations).toBe(2);
  });

  test("navigate to consultation details and assert metadata", async ({ page }) => {
    await page.locator('#consultations-consultation').getByRole('link', { name: 'Consultations' }).click();
    await page.waitForLoadState("networkidle");
    await expect(page).toHaveURL(/\/admin\/consultations\/consultation/);

    const testConsultations = await page.getByRole('link', { name: 'Test Consultation' }).count();
    expect(testConsultations).toBe(2);
    await page.getByRole('link', { name: 'Test Consultation' }).first().click();
    await page.waitForLoadState("networkidle");
    await expect(page).toHaveURL(/\/admin\/consultations\/consultation\/.+/);

    await expect(page.getByRole('heading', { name: 'Test Consultation' })).toBeVisible();
    const title = await page.getByRole('heading', { name: 'Test Consultation' }).textContent();
    const titleInput = await page.getByRole('textbox', { name: 'Title:' }).inputValue();
    expect(title).toBe(titleInput);

    const userList = page.getByLabel('Users:');
    await expect(userList).toBeVisible();
    const userListItems = await userList.locator('option').count();
    expect(userListItems).toBeGreaterThanOrEqual(2)

    let adminUserExists = false;
    for (let i = 0; i < userListItems; i++) {
      const userItem = userList.locator('option').nth(i);
      await expect(userItem).toBeVisible();
      const userEmail = await userItem.textContent();
      if (userEmail === defaultUser.email) {
        adminUserExists = true;
        break;
      }
    }
    expect(adminUserExists).toBe(true);
  });

  test("navigate to consultation list and attempt to clone", async ({ page }) => {
    await page.locator('#consultations-consultation').getByRole('link', { name: 'Consultations' }).click();
    await page.waitForLoadState("networkidle");
    await expect(page).toHaveURL(/\/admin\/consultations\/consultation/);

    const checkbox = page.getByRole('checkbox', { name: 'Select this object for an action - Test Consultation at Analysis Stage' });
    await expect(checkbox).toBeVisible();
    await checkbox.check();
    await expect(checkbox).toBeChecked();

    const actionSelect = page.getByLabel('Action: --------- Delete');
    await expect(actionSelect).toBeVisible();
    await actionSelect.selectOption('create_cloned_consultation');
    await expect(actionSelect).toHaveValue('create_cloned_consultation');

    const goButton = page.getByRole('button', { name: 'Run' });
    await expect(goButton).toBeVisible();
    await goButton.click();
    await page.waitForLoadState("networkidle");
    await expect(page).toHaveURL(/\/admin\/consultations\/consultation/);
  });

  test("navigate to consultation list and attempt to delete", async ({ page }) => {
    await page.locator('#consultations-consultation').getByRole('link', { name: 'Consultations' }).click();
    await page.waitForLoadState("networkidle");
    await expect(page).toHaveURL(/\/admin\/consultations\/consultation/);

    const checkbox = page.getByRole('checkbox', { name: 'Select this object for an action - Test Consultation at Analysis Stage' });
    await expect(checkbox).toBeVisible();
    await checkbox.check();
    await expect(checkbox).toBeChecked();

    const actionSelect = page.getByLabel('Action: --------- Delete');
    await expect(actionSelect).toBeVisible();
    await actionSelect.selectOption('delete_selected');
    await expect(actionSelect).toHaveValue('delete_selected');

    const goButton = page.getByRole('button', { name: 'Run' });
    await expect(goButton).toBeVisible();
    await goButton.click();
    await page.waitForLoadState("networkidle");
    await expect(page).toHaveURL(/\/admin\/consultations\/consultation/);

    const confirmButton = page.getByRole('button', { name: "Yes, I'm sure" });
    await expect(confirmButton).toBeVisible();
    await confirmButton.click();
    await page.waitForLoadState("networkidle");
    await expect(page).toHaveURL(/\/admin\/consultations\/consultation/);

    const testConsultations = await page.getByRole('link', { name: 'Test Consultation' }).count();
    expect(testConsultations).toBe(1);
  });

  test.afterEach(async () => {
    await cleanupManager.cleanup();
  });
});
