import { test, expect } from '@playwright/test';


const BUTTON_NAMES = [
  "View Evaluation",
  "Theme Sign Off",
  "View Dashboard",
]

test(`initially displaying loading message`, async ({ page }) => {
  await page.goto("/consultations/");

  await expect(page.getByText("Loading consultations")).toBeVisible();
})

BUTTON_NAMES.forEach(name => {
  test(`displays ${name} links for each consultation`, async ({ page }) => {
    await page.goto("/consultations/");
    await page.waitForLoadState('networkidle');

    const links = await page.getByRole("button", { name: name }).all();
    expect(links).toHaveLength(3);
  })
})

test(`displays the user's consultations`, async ({ page }) => {
  await page.goto("/consultations/");
  await page.waitForLoadState('networkidle');

  await expect(page.getByText("Dummy Consultation at Analysis Stage")).toBeVisible();
  await expect(page.getByText("Dummy Consultation at Theme Sign Off Stage")).toBeVisible();  
})
