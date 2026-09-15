import { test } from "@playwright/test";

import {
  createFixtureData,
  CleanupManager,
} from "./helpers";
import { finalisingThemesConfirmedConsultation } from "../fixtures";

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
});
