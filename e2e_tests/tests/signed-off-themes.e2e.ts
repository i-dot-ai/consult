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

  [
    { count: 2, names: ["Quality Standards", "Consumer Protection"] },
    { count: 2, names: ["Industry Impact", "Market Competition"] },
    { count: 3, names: ["Implementation Timeline", "Compliance Costs", "Regional Variations"] },
  ].forEach((expectedThemes, index) => {
    test(`should display signed off pill for question ${index + 1}`, async ({ page }) => {
      await page.goto(
        `/consultations/${consultationId}/finalising-themes/${questionIds[index]}`
      );
      await page.waitForLoadState("networkidle");

      await expect(page.getByText("Signed Off").first()).toBeVisible();
      expect(await page.getByText("Signed Off").count()).toBeGreaterThanOrEqual(expectedThemes.count);

      if (index === 0) {
        await expect(page.getByText("Themes finalised")).toBeVisible();
        await expect(page.getByRole("heading", { name: "Selected Themes" })).toBeVisible();
      }

      for (const themeName of expectedThemes.names) {
        await expect(page.getByText(themeName).first()).toBeVisible();
      }
    });
  });

  test("consultation should be in analysis stage", async ({ page }) => {
    await page.goto(`/consultations/${consultationId}`);
    await page.waitForLoadState("networkidle");

    await expect(page.getByText(signedOffConsultation.title).first()).toBeVisible();
    await expect(page.getByTestId("question-card")).toHaveCount(3);
  });
});
