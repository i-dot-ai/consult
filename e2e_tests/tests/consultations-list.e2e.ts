import { test, expect } from '@playwright/test';


let testConsultations;

test.beforeAll(async ({ request }) => {
  const consultationsResponse = await request.get(`/api/consultations/?scope=assigned`);
  const consultationsResponseBody = await consultationsResponse.json();
  testConsultations = consultationsResponseBody.results;
})

test(`initially displaying loading message`, async ({ page }) => {
  await page.goto("/consultations/");

  await expect(page.getByText("Loading consultations")).toBeVisible();
})

test(`displays links for each consultation`, async ({ page }) => {
  await page.goto("/consultations/");
  await page.waitForLoadState('networkidle');

  testConsultations.forEach(async consultation => {
    const evaluationLink = await page.locator(`a[href="/evaluations/${consultation.id}/questions/"]`);
    expect(evaluationLink).toBeVisible();

    const dashboardLink = await page.locator(`a[href="/consultations/${consultation.id}"]`);
    expect(dashboardLink).toBeVisible();

    const themeSignOffLink = await page.locator(`a[href="/consultations/${consultation.id}/theme-sign-off"]`);
    expect(themeSignOffLink).toBeVisible();
  })
})

test(`displays the user's consultations`, async ({ page }) => {
  await page.goto("/consultations/");
  await page.waitForLoadState('networkidle');

  testConsultations.forEach(async consultation => {
    await expect(page.getByText(consultation.title, { exact: true })).toBeVisible();
  })
})
