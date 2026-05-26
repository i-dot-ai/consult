import { test, expect } from '@playwright/test';

import {
  createFixtureData,
  deleteFixtureData,
  deleteUser,
  getFirstConsultationLink
} from './helpers';
import { defaultUser, setupConsultation } from '../fixtures';
import type { FixtureReference } from "../fixtures";


test.describe('Users Page', () => {
  let uniqueEmail: string;

  test.beforeEach(async ({ page }) => {
    await page.goto('/support/users');
    await page.waitForLoadState('networkidle');
  });

  test('adding a user that already exists shows an error message', async ({ page }) => {
    // Click the "Add User" button to open the form
    await page.locator('a[href="/support/users/new"]').click();
    // Check if form is open
    await expect(page).toHaveURL(/\/support\/users\/new/);
    await page.waitForLoadState('networkidle');
    // Fill in the form with an existing user's email
    await page.getByRole('textbox', { name: /email/i }).fill(defaultUser.email);
    // Submit the form
    await page.getByRole('button', { name: 'Add user' }).click();
    // Check for the error message indicating the user already exists
    await expect(page.getByText('Error: user with this email address already exists.')).toBeVisible();
  });

  test('adding a user with valid details succeeds', async ({ page }) => {
    // Click the "Add User" button to open the form
    await page.locator('a[href="/support/users/new"]').click();
    // Check if form is open
    await expect(page).toHaveURL(/\/support\/users\/new/);
    await page.waitForLoadState('networkidle');
    // Fill in the form with valid details
    uniqueEmail = `testuser${Date.now()}@example.com`;
    await page.getByRole('textbox', { name: /email/i }).fill(uniqueEmail);
    // Submit the form
    await page.getByRole('button', { name: 'Add user' }).click();
    // Check that it goes back to users list page
    await expect(page).toHaveURL(/\/support\/users/);
    await page.waitForLoadState('networkidle');
    // Check new user appears in the list
    await expect(page.getByText(uniqueEmail)).toBeVisible()
  });

  test.afterEach(async () => {
    if (uniqueEmail) {
      await deleteUser(uniqueEmail);
    }
  });

});

test.describe('Consultation Details - Adding Users', () => {

  let testData: FixtureReference = {};

  test.beforeAll(async ({ request }) => {
    testData = await createFixtureData(request, {
      consultations: [setupConsultation],
    });
  });

  test.beforeEach(async ({ page }) => {
    await page.goto('/support/consultations');
    await page.waitForLoadState('networkidle');
  });

  test('Ensure that adding a user to a consultation persists and shows up in the consultation details', async ({ page }) => {
    // Navigate to the consultation details page
    const result = await getFirstConsultationLink(page);
    expect(result).toBeTruthy();
    const consultationId = result!.href.match(/\/consultations\/([^/]+)/)?.[1];
    await page.goto(`/support/consultations/${consultationId}/users/new`);
    await page.waitForLoadState('networkidle');
    // Fill in the form with valid details
    await page.getByRole('textbox', { name: /email/i }).fill(defaultUser.email);
    // Submit the form
    await page.getByRole('button', { name: /Add users/i }).click();
    await expect(page.getByText("Successfully added 1 users to consultation.")).toBeVisible();
    // Go back to consultation details page
    await page.goto(`/support/consultations/${consultationId}`);
    await page.waitForLoadState('networkidle');
    // Check that the user appears in the consultation details page
    await expect(page.getByText(defaultUser.email)).toBeVisible();
  });

  test.afterAll(async () => {
    await deleteFixtureData(testData);
  });

});
