import { test, expect, Page } from '@playwright/test';


let consultation;
let consultationQuestions;

let signedOffQuestion;
let signedOffQuestionThemes;
let draftQuestion;
let draftQuestionSelectedThemes;
let draftQuestionGeneratedThemes;

test.beforeAll(async ({ request }) => {
  const consultationsResponse = await request.get(`/api/consultations/?scope=assigned`);
  const consultationsResponseBody = await consultationsResponse.json();
  consultation = consultationsResponseBody.results.find(consultation => consultation.stage === "theme_sign_off");

  const questionsResponse = await request.get(`/api/consultations/${consultation.id}/questions/`);
  const questionsResponseBody = await questionsResponse.json();
  consultationQuestions = questionsResponseBody.results;

  signedOffQuestion = consultationQuestions.find(question => question.theme_status === "confirmed");
  draftQuestion = consultationQuestions.find(question => question.theme_status === "draft");
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

  test(`clicking Select Another Question button navigates away`, async ({ page }) => {
    const supportButton = page.getByRole("button", { name: "Select Another Question" });

    await supportButton.click();

    await expect(page).toHaveURL(`/consultations/${consultation.id}/theme-sign-off`);
  })

  test(`clicking Back to Questions button navigates away`, async ({ page }) => {
    const supportButton = page.getByRole("button", { name: "Back to Questions" });

    await supportButton.click();

    await expect(page).toHaveURL(`/consultations/${consultation.id}/theme-sign-off`);
  })

  test(`displays question title`, async ({ page }) => {
    await page.waitForLoadState('networkidle');

    const expectedTitle = `Q${signedOffQuestion.number}: ${signedOffQuestion.question_text}`;

    await expect(page.getByText(expectedTitle, { exact: true })).toBeVisible();
  })
})

test.describe("draft question", () => {
  // Uncomment to run tests serially
  test.describe.configure({ mode: "serial" });

  test.beforeEach(async ({ page, request }) => {
    const selectedThemesResponse = await request.get(`/api/consultations/${consultation.id}/questions/${draftQuestion.id}/selected-themes/`);
    const selectedThemes = await selectedThemesResponse.json();
    draftQuestionSelectedThemes = selectedThemes.results;

    const generatedThemesResponse = await request.get(`/api/consultations/${consultation.id}/questions/${draftQuestion.id}/candidate-themes/`);
    const generatedThemes = await generatedThemesResponse.json();
    draftQuestionGeneratedThemes = generatedThemes.results;

    await page.goto(`/consultations/${consultation.id}/theme-sign-off/${draftQuestion.id}`);
  })

  test(`does not display signed off message`, async ({ page }) => {
    expect(page.getByText("Themes Signed Off")).not.toBeVisible();
  })

  test(`displays total response count`, async ({ page }) => {
    await page.waitForLoadState("networkidle");

    expect(page.getByText(`${draftQuestion.total_responses} responses`)).toBeVisible();
  })

  test(`displays question title`, async ({ page }) => {
    await page.waitForLoadState("networkidle");

    expect(page.getByText(`Q${draftQuestion.number}: ${draftQuestion.question_text}`)).toBeVisible();
  })

  test(`clicking "Choose another question" button navigates away`, async ({ page }) => {
    const supportButton = page.getByRole("button", { name: "Choose another question" });

    await supportButton.click();

    await expect(page).toHaveURL(`/consultations/${consultation.id}/theme-sign-off`);
  })

  test(`selected themes count is displayed`, async ({ page }) => {
    await page.waitForLoadState("networkidle");

    await expect(page.getByText(`${draftQuestionSelectedThemes.length} selected`, { exact: true })).toBeVisible();
  })

  test(`selected theme names are displayed`, async ({ page }) => {
    await page.waitForLoadState("networkidle");

    const NEW_THEME_NAME = "selected-theme-names-test";

    await createSelectedTheme(page, NEW_THEME_NAME);

    [...draftQuestionSelectedThemes, { name: NEW_THEME_NAME }].forEach(theme => {
      expect(page.getByRole("heading", { name: theme.name })).toBeVisible();
    })

    await deleteSelectedTheme(page, NEW_THEME_NAME);
  })

  test(`selected theme descriptions are displayed`, async ({ page }) => {
    await page.waitForLoadState("networkidle");

    draftQuestionSelectedThemes.forEach(theme => {
      expect(page.getByText(theme.description, { exact: true })).toBeVisible();
    })
  })

  test(`selected theme users are displayed`, async ({ page }) => {
    await page.waitForLoadState("networkidle");

    const userEmails = [...new Set(draftQuestionSelectedThemes.map(theme => theme.last_modified_by))];

    userEmails.forEach(async userEmail => {
      const allOccurences = await page.getByText(userEmail as string).all();
      // might appear more than once
      expect(allOccurences.length).toBeGreaterThanOrEqual(1);
    })
  })

  test(`clicking "Add Custom Theme" button reveals add theme panel`, async ({ page }) => {
    await page.waitForLoadState("networkidle");

    expect(page.getByRole("heading", { name: "Add Custom Theme" })).not.toBeVisible();

    await page.getByRole("button", { name: "Add Custom Theme" }).click();

    expect(page.getByRole("heading", { name: "Add Custom Theme" })).toBeVisible();
  })

  test(`clicking "Creating Effective Themes" button reveals instructions`, async ({ page }) => {
    await page.waitForLoadState("networkidle");

    await page.getByRole("button", { name: "Add Custom Theme" }).click();

    const instructionsButton = await page.getByRole("button", { name: "Creating Effective Themes" });
    await expect(instructionsButton).toBeVisible();

    expect(page.getByRole("heading", { name: "Good theme titles:" })).not.toBeVisible();
    expect(page.getByRole("heading", { name: "Good theme descriptions:" })).not.toBeVisible();

    await instructionsButton.click();

    await expect(page.getByRole("heading", { name: "Good theme titles:" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Good theme descriptions:" })).toBeVisible();
  })

  test(`clicking "Cancel" button hides add theme panel`, async ({ page }) => {
    await page.waitForLoadState("networkidle");

    await page.getByRole("button", { name: "Add Custom Theme" }).click();

    // Panel is revealed
    await expect(page.getByRole("heading", { name: "Add Custom Theme" })).toBeVisible();

    await page.getByRole("button", { name: "Cancel" }).click();

    // Panel is hidden
    await expect(page.getByRole("heading", { name: "Add Custom Theme" })).not.toBeVisible();
  })

  test(`adding new theme form adds new theme`, async ({ page }) => {
    await page.waitForLoadState("networkidle");
    const NEW_THEME_NAME = "theme-create-form-test";

    await createSelectedTheme(page, NEW_THEME_NAME);

    await deleteSelectedTheme(page, NEW_THEME_NAME);
  })

  test(`clicking "Representative Responses" button reveals responses panel`, async ({ page }) => {
    await page.waitForLoadState("networkidle");

    const NEW_THEME_NAME = "representative-responses-test";
    await createSelectedTheme(page, NEW_THEME_NAME);

    const responsesButtons = await page.getByRole("button", { name: "Representative Responses" }).all();

    expect(responsesButtons.length).toBeGreaterThanOrEqual(1);
    await responsesButtons.at(0)!.click();

    await expect(page.getByRole("heading", { name: "Representative Responses" })).toBeVisible();

    await expect(page.locator(".theme-sign-off__answers-list li").or(page.getByText("There are no answers"))).toBeVisible();

    await deleteSelectedTheme(page, NEW_THEME_NAME);
  })

  test(`clicking "Edit" button reveals and "Cancel" hides edit panel`, async ({ page }) => {
    await page.waitForLoadState("networkidle");

    const NEW_THEME_NAME = "edit-button-reveal-panel-test";
    await createSelectedTheme(page, NEW_THEME_NAME);

    const editButton = page.getByLabel(`Edit Theme ${NEW_THEME_NAME}`);
    expect(editButton).toBeVisible();

    await editButton.click();

    await expect(page.getByRole("heading", { name: "Edit Theme" })).toBeVisible();

    await page.getByRole("button", { name: "Cancel" }).click();

    await deleteSelectedTheme(page, NEW_THEME_NAME);
  })

  test(`clicking sign off button reveals sign off confirmation modal`, async ({ page }) => {
    await page.waitForLoadState("networkidle");

    const NEW_THEME_NAME = "edit-button-reveal-panel-test";
    await createSelectedTheme(page, NEW_THEME_NAME);

    const signOffButton = page.getByRole("button", { name: `Sign Off Selected Themes (${draftQuestionSelectedThemes.length + 1 })` });
    expect(signOffButton).toBeVisible();

    await signOffButton.click();

    await expect(page.getByRole("heading", { name: "Confirm Theme Sign Off"})).toBeVisible();

    [...draftQuestionSelectedThemes, { name: NEW_THEME_NAME}].forEach(async theme => {
      // appears twice, one in regular list, one in confirm modal
      const headings = await page.getByRole("heading", { name: theme.name }).all();
      await expect(headings).toHaveLength(2);
    })

    await expect(page.getByRole("button", { name: "Confirm Sign Off" })).toBeVisible();

    await page.getByRole("button", { name: "Cancel"}).click();

    await expect(page.getByRole("heading", { name: "Confirm Theme Sign Off"})).not.toBeVisible();

    await deleteSelectedTheme(page, NEW_THEME_NAME);
  })

  test("displays browse text", async ({ page }) => {
    await expect(page.getByText("Browse AI Generated Themes")).toBeVisible();
  })

  test("displays all generated themes", async ({ page }) => {
    await page.waitForLoadState("networkidle");
    draftQuestionGeneratedThemes.forEach(async theme => {
      await expect(page.getByRole("heading", { name: theme.name })).toBeVisible();
    })
  })

  test("displays level 1 tags for all parent themes", async ({ page, request }) => {
    await page.waitForLoadState("networkidle");

    const levelOneTags = await page.getByText("Level 1").all();

    expect(levelOneTags).toHaveLength(draftQuestionGeneratedThemes.length);
  })
})

const createSelectedTheme = async (page: Page, name: string, description?: string) => {
  // Reveal add theme panel
  await page.getByRole("button", { name: "Add Custom Theme" }).click();

  const titleInput = page.getByLabel("Theme Title");
  const descriptionInput = page.getByLabel("Theme Description");
  const addThemeButton = page.getByRole("button", { name: "Add Theme" });
  expect(titleInput).toBeVisible();
  expect(descriptionInput).toBeVisible();
  expect(addThemeButton).toBeVisible();
  expect(addThemeButton).toBeDisabled();

  // Create new theme
  await titleInput.fill(name);
  await descriptionInput.fill(description || "New test theme description");
  await addThemeButton.click();

  // Confirm new theme is listed among selected themes
  await expect(page.getByRole("heading", { name: name })).toBeVisible();
}

const deleteSelectedTheme = async (page: Page, name: string) => {
  // Remove the new theme
  const removeButton = await page.getByLabel(`Remove Theme ${name}`);
  await removeButton.click();
  await expect(page.getByRole("heading", { name: name })).not.toBeVisible();
}