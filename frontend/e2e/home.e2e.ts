import { test, expect } from "@playwright/test";
import { execSync } from 'child_process';

test("get started link", async ({ page }) => {
  await page.goto("/");

  const getInvolvedButtons = await page
    .getByRole("link", { name: "Get involved" })
    .all();

  getInvolvedButtons.at(0)!.click();

  await expect(
    page.getByRole("heading", { name: "Get involved" }),
  ).toBeVisible();
});

test("has title", async ({ page }) => {
  await page.goto("/");

  await expect(page).toHaveTitle(/Consult/);
});

test("redirects to sign-in when accessing protected consultation route", async ({ page }) => {
  await page.goto("/support/consultations/");
  
  await expect(page).toHaveURL(/\/sign-in/);
});

test("can enter email and submit sign-in form", async ({ page }) => {
  await page.goto("/sign-in/");
  
  await page.fill('input[type="email"]', "email@example.com");
  await page.click('button[type="submit"], input[type="submit"]');
});


test.describe.serial('Magic link authentication', () => {
  test("can complete magic link flow", async ({ page }) => {
  await page.goto("/sign-in/");
  
  // Submit email
  await page.fill('input[type="email"]', "email@example.com");
  await page.click('button[type="submit"], input[type="submit"]');
  
  // Wait a moment for the backend to process
  await page.waitForTimeout(2000);
  
  // Get recent backend logs to extract magic link
  const logs = execSync('docker compose logs --tail=50 backend', { encoding: 'utf8' });
  
  // Extract ALL magic links and get the last one
  const magicLinkMatches = [...logs.matchAll(/magic_link":\s*"([^"]+)"/g)];
  const magicLinkMatch = magicLinkMatches.length > 0 ? magicLinkMatches[magicLinkMatches.length - 1] : null;
  
  if (magicLinkMatch) {
    const magicLink = magicLinkMatch[1];
    console.log("ML:", magicLink);
    
    // Navigate to the magic link
    await page.goto(magicLink);
    
    // Verify we're on the magic link page
    await expect(page).toHaveURL(/\/magic-link\//);
    await expect(page.getByRole("heading", { name: "Confirm sign in" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Sign in" })).toBeVisible();
    
    
    // Click the "Sign in" button
    await page.getByRole("button", { name: "Sign in" }).click();
     
    // Try to see if we got redirected successfully
    await expect(page).toHaveURL(/\/consultations/);
  }
  });
});
