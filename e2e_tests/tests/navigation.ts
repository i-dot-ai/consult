import { expect } from "@playwright/test";
import type { Page } from "@playwright/test";

// Onboarding tours overlay the page until dismissed. The list page uses the
// "-archive" key; the detail page additionally uses the "-finalising-themes"
// key. Dismissing both is harmless on either page.
const FINALISE_THEMES_ONBOARDING_KEYS = [
  "onboardingComplete-finalising-themes-archive",
  "onboardingComplete-finalising-themes",
];

/**
 * Navigates from the consultations list to the finalise themes list page for
 * the given consultation. By default the onboarding tours are dismissed so
 * they do not overlay the page.
 */
export async function gotoFinaliseThemesList(
  page: Page,
  consultationTitle: string,
  { dismissOnboarding = true }: { dismissOnboarding?: boolean } = {},
) {
  await page.goto("/consultations");
  await page.waitForLoadState("networkidle");

  if (dismissOnboarding) {
    await page.evaluate(
      (keys) => keys.forEach((key) => localStorage.setItem(key, "true")),
      FINALISE_THEMES_ONBOARDING_KEYS,
    );
  }

  const finaliseThemesLink = page.getByTestId(
    `Finalise Themes for ${consultationTitle}`,
  );
  // Guard against a duplicate testId regression before clicking.
  await expect(finaliseThemesLink).toHaveCount(1);
  await finaliseThemesLink.click();
  await page.waitForLoadState("networkidle");

  // The page is rendered with client:only, so questions are fetched after
  // hydration. Wait for the cards to render before asserting on the
  // client-rendered content (count, stage panel, tags, etc.).
  await expect(page.getByTestId("question-card").first()).toBeVisible();
}
