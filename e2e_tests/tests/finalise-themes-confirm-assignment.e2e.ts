import { test, expect } from "@playwright/test";
import { ListObjectsV2Command } from "@aws-sdk/client-s3";

import {
  createFixtureData,
  makeMinioClient,
  CleanupManager,
} from "./helpers";
import { gotoFinaliseThemesList } from "./navigation";
import { finalisingThemesConfirmedConsultation } from "../fixtures";
import { S3_BUCKET, testAccessToken } from "../constants";

test.describe.configure({ mode: "serial" });
const cleanupManager = new CleanupManager();

test.describe("Finalise Themes - Confirm and Proceed to Assignment", () => {
  let consultationId: string;
  let consultationCode: string | undefined;

  test.beforeAll(async ({ request }) => {
    const testData = await createFixtureData(request, {
      consultations: [finalisingThemesConfirmedConsultation],
    });
    cleanupManager.add(testData);
    consultationId = testData.consultation_ids![0];
    consultationCode = finalisingThemesConfirmedConsultation.code;
  });

  test.afterAll(async () => {
    await cleanupManager.cleanup();
  });

  test("confirms themes, uploads to S3 and advances to assigning_themes", async ({
    page,
  }) => {
    await gotoFinaliseThemesList(page, finalisingThemesConfirmedConsultation.title);

    const proceedButton = page.getByRole("button", {
      name: "Confirm and Proceed to Assignment",
    });
    await expect(proceedButton).toBeEnabled();

    // Open the confirm modal
    await proceedButton.click();
    await expect(
      page.getByRole("heading", { name: "Confirm AI Assignment" }),
    ).toBeVisible();

    // Confirming fires assign-themes
    const assignResponse = page.waitForResponse(
      (r) =>
        r.url().includes(`/consultations/${consultationId}/assign-themes`) &&
        r.request().method() === "POST",
    );
    await page.getByRole("button", { name: "Yes, Start AI Assignment" }).click();

    expect((await assignResponse).status()).toBe(202);

    // The selected-themes CSV is sent to Minio
    const s3 = makeMinioClient();
    const prefix = `app_data/consultations/${consultationCode}/inputs/`;
    await expect
      .poll(
        async () => {
          const out = await s3.send(
            new ListObjectsV2Command({ Bucket: S3_BUCKET, Prefix: prefix }),
          );
          return (out.Contents ?? []).some((o) => o.Key?.endsWith("themes.csv"));
        },
        { timeout: 15000 },
      )
      .toBe(true);

    // Consultation stage advances to assigning_themes
    await expect
      .poll(
        async () => {
          const response = await page.request.get(`/api/consultations/${consultationId}/`, {
            headers: { Authorization: `Bearer ${testAccessToken}` },
          });
          const data = await response.json();
          return data.stage;
        },
        { timeout: 10000 },
      )
      .toBe("assigning_themes");

    // After success
    await expect(
      page.getByRole("heading", { name: "Confirm AI Assignment" }),
    ).toBeHidden();
    await expect(proceedButton).toBeHidden();
  });
});
