import { test, expect } from '@playwright/test';


const SECTION_TITLES = [
  "Theme Sign Off",
  "All consultation questions",
];

const CONSULTATION_STAGES = [
  "Set up data",
  "Find themes (AI)",
  "Finalise themes",
  "Assign themes (AI)",
  "Check quality",
  "Analyse",
];

let testConsultation;
let testConsultationQuestions;

test.beforeAll(async ({ request }) => {
  const consultationsResponse = await request.get(`/api/consultations/?scope=assigned`);
  const consultationsResponseBody = await consultationsResponse.json();
  testConsultation = consultationsResponseBody.results[0];

  const questionsResponse = await request.get(`/api/consultations/${testConsultation.id}/questions/`);
  const questionsResponseBody = await questionsResponse.json();
  testConsultationQuestions = questionsResponseBody.results;
});

test.beforeEach(async ({ page }) => {
  await page.goto(`/consultations/${testConsultation.id}/theme-sign-off`);
})

test(`initially displays loading messages`, async ({ page }) => {
  await expect(page.getByText("Loading Questions")).toBeVisible();
})

test(`displays header sub path text`, async ({ page }) => {
  const subpathEl = page.getByTestId("header-subpath");
  await expect(subpathEl).toBeVisible();
  await expect(subpathEl).toContainText("Theme Sign Off");
})

SECTION_TITLES.forEach(title => {
  test(`displays section titles: ${title}`, async ({ page }) => {
    await expect(page.getByRole("heading", { name: title, exact: true })).toBeVisible();
  })
})

test(`displays questions`, async ({ page }) => {
  await page.waitForLoadState('networkidle');

  testConsultationQuestions.forEach(async question => {
    const questionText = `Q${question.number}: ${question.question_text}`;
    await expect(page.getByText(questionText, { exact: true })).toBeVisible({ timeout: 5000 });
  })
})

test(`searching questions updates question list`, async ({ page }) => {
  await page.waitForLoadState('networkidle');

  page.getByRole('textbox').fill(`Text that won't match anything`);

  await expect(page.getByText("No questions found matching your search")).toBeVisible();
})

test(`renders onboarding modal initially`, async ({ page }) => {
  await page.waitForLoadState('networkidle');

  await expect(page.getByRole("heading", { name: "Welcome to Theme Sign Off" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Get Started" })).toBeVisible();
})

test(`closes onboarding modal if close button is clicked`, async ({ page }) => {
  await page.waitForLoadState('networkidle');

  const modalCloseButton = page.getByText("Get Started");
  await modalCloseButton.click();

  await expect(page.getByRole("heading", { name: "Welcome to Theme Sign Off" })).not.toBeVisible();
  await expect(page.getByRole("button", { name: "Get Started" })).not.toBeVisible();
})

test(`renders process button`, async ({ page }) => {
  const processButton = page.getByRole("button", { name: "Process" });
  await expect(processButton).toBeVisible();
  await expect(processButton).toHaveAttribute("aria-pressed", "false");
})

test(`renders breadcrumbs when process button is clicked`, async ({ page }) => {
  const processButton = page.getByRole("button", { name: "Process" });

  await expect(processButton).toBeVisible();
  await processButton.click();

  // await page.waitForTimeout(500);
  await page.waitForLoadState("domcontentloaded");

  await expect(processButton).toHaveAttribute("aria-pressed", "true"); // , {timeout: 5000});
  await expect(page.locator(`[aria-label="breadcrumbs"]`)).toBeVisible();

  CONSULTATION_STAGES.forEach(async stage => {
    await expect(page.getByText(stage, { exact: true })).toBeVisible();
  });
})

test(`closes breadcrumbs if process button is clicked while breadcrumbs is visible`, async ({ page }) => {
  const processButton = page.getByRole("button", { name: "Process" });

  await expect(page.locator(`[aria-label="breadcrumbs"]`)).not.toBeVisible();

  await processButton.click();

  await page.waitForLoadState("domcontentloaded");

  await expect(page.locator(`[aria-label="breadcrumbs"]`)).toBeVisible();

  await processButton.click();

  await expect(page.locator(`[aria-label="breadcrumbs"]`)).not.toBeVisible();
  await expect(processButton).toHaveAttribute("aria-pressed", "false");
})

test(`renders guidance link when process button is clicked`, async ({ page }) => {
  const processButton = page.getByRole("button", { name: "Process" });

  await expect(processButton).toBeVisible();
  processButton.click();

  const guidanceLink = page.getByRole("link", { name: "Explain the process" });
  await expect(guidanceLink).toBeVisible();
  await expect(guidanceLink).toHaveAttribute("href", "/guidance");
})

test(`favourites and unfavourites a question if button is clicked`, async ({ page }) => {
  await page.waitForSelector(`[data-testid="fav-button"]`);

  // Close onboarding modal
  const modalCloseButton = page.getByText("Get Started");
  await modalCloseButton.click();

  // localStorage value starts as null
  await page.waitForFunction(() => {
    return localStorage.getItem("favouritedQuestions") === null;
  })

  const favButtons = await page.getByTestId("fav-button").all();
  const firstFavButton = favButtons.at(0);

  // button is clicked, localStorage value has the question ID in an array
  const expectedValue = `["${testConsultationQuestions.at(0).id}"]`;
  await firstFavButton!.click();
  await page.waitForFunction((expectedValue) => {
    return localStorage.getItem("favouritedQuestions") === expectedValue;
  }, expectedValue)

  // button is clicked again, localStorage value is now empty array
  await firstFavButton!.click();
  await page.waitForFunction(() => {
    return localStorage.getItem("favouritedQuestions") === "[]";
  })
})