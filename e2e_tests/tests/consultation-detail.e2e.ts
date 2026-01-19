import { test, expect } from '@playwright/test';


const SECTION_TITLES = [
  "Key Metrics",
  "Favourited questions",
  "All consultation questions",
]

let exampleConsultation;
let exampleConsultationQuestions;

test.beforeAll(async ({ request }) => {
  const consultationsResponse = await request.get(`/api/consultations/?scope=assigned`);
  const consultationsResponseBody = await consultationsResponse.json();
  exampleConsultation = consultationsResponseBody.results[0];

  const questionsResponse = await request.get(`/api/consultations/${exampleConsultation.id}/questions/`);
  const questionsResponseBody = await questionsResponse.json();
  exampleConsultationQuestions = questionsResponseBody.results;
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

test(`displays questions`, async ({ page }) => {
  await page.waitForLoadState('networkidle');

  exampleConsultationQuestions.forEach(question => {
    const questionText = `Q${question.number}: ${question.question_text}`;
    expect(page.getByText(questionText, { exact: true })).toBeVisible();
  })
})

test(`searching questions updates question list`, async ({ page }) => {
  await page.waitForLoadState('networkidle');

  page.getByRole('textbox').fill(`Text that won't match anything`);

  expect(page.getByText("No questions found matching your search")).toBeVisible();
})

test(`favourites and unfavourites a question if button is clicked`, async ({ page }) => {
  await page.waitForLoadState('networkidle');

  // localStorage value starts as null
  await page.waitForFunction(() => {
    return localStorage.getItem("favouritedQuestions") === null;
  })

  const favButtons = await page.getByTestId("fav-button").all();
  const firstFavButton = favButtons.at(0);

  // button is clicked, localStorage value has the question ID in an array
  const expectedValue = `["${exampleConsultationQuestions.at(0).id}"]`;
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