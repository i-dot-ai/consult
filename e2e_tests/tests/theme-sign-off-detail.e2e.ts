import { test, expect } from '@playwright/test';


let consultation;
let consultationQuestions;

let signedOffQuestion;
let signedOffQuestionThemes;
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
  test.beforeEach(async ({ page, request }) => {

    const themesResponse = await request.get(`/api/consultations/${consultation.id}/questions/${signedOffQuestion.id}/selected-themes/`);
    const themes = await themesResponse.json();
    signedOffQuestionThemes = themes.results;

    await page.goto(`/consultations/${consultation.id}/theme-sign-off/${signedOffQuestion.id}`);
  })

  test(`displays signed off message`, async ({ page }) => {
    expect(page.getByText("Themes Signed Off")).toBeVisible();
  })

  test(`displays themes`, async ({ page }) => {
    await page.waitForLoadState('networkidle');

    signedOffQuestionThemes.forEach(theme => {
      expect(page.getByText(theme.name)).toBeVisible();
    })
  })

  test(`displays signed off tags for all themes`, async ({ page }) => {
    await page.waitForLoadState('networkidle');

    const signedOffLabels = await page.getByText("Signed Off", { exact: true }).all();
    expect(signedOffLabels).toHaveLength(signedOffQuestionThemes.length);
  })

  test(`displays support button`, async ({ page }) => {
    expect(page.getByRole("button", { name: "consult@cabinetoffice.gov.uk" })).toBeVisible();
  })

  test(`clicking support button triggers email client`, async ({ page }) => {
    const supportButton = page.getByRole("button", { name: "consult@cabinetoffice.gov.uk" });

    const [ request ] = await Promise.all([
      page.waitForEvent("request", request => request.url().startsWith("mailto:")),
      supportButton.click(),
    ])

    expect(request.url()).toBe("mailto:consult@cabinetoffice.gov.uk");
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
