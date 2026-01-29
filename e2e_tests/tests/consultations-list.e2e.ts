import { test, expect } from '@playwright/test';


let consultations;

test.beforeAll(async ({ request }) => {
  const consultationsResponse = await request.get(`/api/consultations/?scope=assigned`);
  const consultationsResponseBody = await consultationsResponse.json();
  consultations = consultationsResponseBody.results;
})

test(`initially displaying loading message`, async ({ page }) => {
  await page.goto("/consultations/");

  await expect(page.getByText("Loading consultations")).toBeAttached();
})

test(`displays links for each consultation`, async ({ page }) => {
  await page.goto("/consultations/");
  await page.waitForLoadState('networkidle');

  consultations.forEach(async consultation => {
    const evaluationLink = page.locator(`a[href="/evaluations/${consultation.id}/questions/"]`);
    expect(evaluationLink).toBeAttached();

    const dashboardLink = page.locator(`a[href="/consultations/${consultation.id}"]`);
    expect(dashboardLink).toBeAttached();

    const themeSignOffLink = page.locator(`a[href="/consultations/${consultation.id}/theme-sign-off"]`);
    expect(themeSignOffLink).toBeAttached();
  })
})

test(`displays the user's consultations`, async ({ page }) => {
  await page.goto("/consultations/");
  await page.waitForLoadState('networkidle');

  consultations.forEach(async consultation => {
    await expect(page.getByText(consultation.title, { exact: true })).toBeAttached();
  })
})
