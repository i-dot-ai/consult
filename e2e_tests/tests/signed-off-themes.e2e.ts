import { test, expect } from "@playwright/test";
import {
  createFixtureData,
  deleteFixtureData,
} from "./helpers";
import { signedOffConsultation } from "../fixtures";
import type { FixtureReference } from "../fixtures";

test.describe("Signed Off Themes", () => {
  let testData: FixtureReference = {};
  let consultationId: string;
  let questionIds: string[];

  test.beforeAll(async ({ request }) => {
    testData = await createFixtureData(request, {
      consultations: [signedOffConsultation],
    });
    consultationId = testData.consultation_ids![0];
    questionIds = testData.question_ids!;
  });

  test.afterAll(async () => {
    await deleteFixtureData(testData);
  });

  test("all questions should display signed off status", async ({ page }) => {
    expect(questionIds).toHaveLength(3);

    await page.goto(`/consultations/${consultationId}/finalising-themes`);
    await page.waitForLoadState("networkidle");

    await expect(page.getByTestId("question-card")).toHaveCount(3);
  });

  test.describe("individual question themes", () => {
    test.beforeEach(async ({ page }, testInfo) => {
      const questionIndex = testInfo.title.includes("first") ? 0 
        : testInfo.title.includes("second") ? 1 
        : 2;
      
      await page.goto(
        `/consultations/${consultationId}/finalising-themes/${questionIds[questionIndex]}`
      );
      await page.waitForLoadState("networkidle");
    });

    test("should display signed off pill for first question", async ({ page }) => {
      await expect(page.getByText("Signed Off").first()).toBeVisible();
      expect(await page.getByText("Signed Off").count()).toBeGreaterThanOrEqual(2);
      await expect(page.getByText("Themes finalised")).toBeVisible();
      await expect(page.getByRole("heading", { name: "Selected Themes" })).toBeVisible();
      await expect(page.locator('text=/Quality Standards/i').first()).toBeVisible();
      await expect(page.locator('text=/Consumer Protection/i').first()).toBeVisible();
    });

    test("should display signed off pill for second question", async ({ page }) => {
      await expect(page.getByText("Signed Off").first()).toBeVisible();
      expect(await page.getByText("Signed Off").count()).toBeGreaterThanOrEqual(2);
      await expect(page.getByText("Industry Impact")).toBeVisible();
      await expect(page.getByText("Market Competition")).toBeVisible();
    });

    test("should display signed off pill for third question", async ({ page }) => {
      await expect(page.getByText("Signed Off").first()).toBeVisible();
      expect(await page.getByText("Signed Off").count()).toBeGreaterThanOrEqual(3);
      await expect(page.getByText("Implementation Timeline")).toBeVisible();
      await expect(page.getByText("Compliance Costs")).toBeVisible();
      await expect(page.getByText("Regional Variations")).toBeVisible();
    });
  });

  test("consultation should be in analysis stage", async ({ page }) => {
    await page.goto(`/consultations/${consultationId}`);
    await page.waitForLoadState("networkidle");

    await expect(page.getByText(signedOffConsultation.title).first()).toBeVisible();
    await expect(page.getByTestId("question-card")).toHaveCount(3);
  });
});
