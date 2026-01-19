import { test, expect } from '@playwright/test';


const SECTION_TITLES = [
  "Key Metrics",
  "Favourited questions",
  "All consultation questions",
]

let exampleConsultation;

test.beforeAll(async ({ request }) => {
  const response = await request.get(`/api/consultations/?scope=assigned`);
  const body = await response.json();
  exampleConsultation = body.results[0];
});

test.beforeEach(async ({ page }) => {
  await page.goto(`/consultations/${exampleConsultation.id}`);
})

test(`initially displays loading messages`, async ({ page }) => {
  expect(page.getByText("Loading Demographics")).toBeVisible();

  const questionsLoadingTexts = await page.getByText("Loading Questions").all();
  expect(questionsLoadingTexts).toHaveLength(3);
})

SECTION_TITLES.forEach(title => {
  test(`displays section titles: ${title}`, async ({ page }) => {
    expect(page.getByText(title)).toBeVisible();
  })
})

test(`displays header sub path text`, async ({ page }) => {
  expect(page.getByText("Dashboard")).toBeVisible();
})
