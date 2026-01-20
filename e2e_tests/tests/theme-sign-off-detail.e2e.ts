import { test, expect } from '@playwright/test';


let consultation;
let consultationQuestions;

let signedOffQuestion;
let inProgressQuestion;

test.beforeAll(async ({ request }) => {
  const consultationsResponse = await request.get(`/api/consultations/?scope=assigned`);
  const consultationsResponseBody = await consultationsResponse.json();
  consultation = consultationsResponseBody.results.find(consultation => consultation.stage === "theme_sign_off");

  const questionsResponse = await request.get(`/api/consultations/${consultation.id}/questions/`);
  const questionsResponseBody = await questionsResponse.json();
  consultationQuestions = questionsResponseBody.results;

  signedOffQuestion = consultationQuestions.find(question => question.theme_status === "confirmed");
  inProgressQuestion = consultationQuestions.find(question => question.theme_status === "draft");
});

test.describe("signed off question", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`/consultations/${consultation.id}/theme-sign-off/${signedOffQuestion.id}`);
  })

  test(`displays signed off message`, async ({ page }) => {
    expect(page.getByText("Themes Signed Off")).toBeVisible();
  })
})

test.describe("draft question", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`/consultations/${consultation.id}/theme-sign-off/${inProgressQuestion.id}`);
  })

  test(`does not display signed off message`, async ({ page }) => {
    expect(page.getByText("Themes Signed Off")).not.toBeVisible();
  })
})
