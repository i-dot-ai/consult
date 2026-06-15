import { expect } from "@playwright/test";
import type { Page } from "@playwright/test";

/**
 * Finds the first consultation link that points to an actual consultation detail
 * page (not the consultations list page itself).
 */
export async function getFirstConsultationLink(page: Page) {
  const allLinks = page.locator('a[href*="/consultations/"]');
  const count = await allLinks.count();

  for (let i = 0; i < count; i++) {
    const link = allLinks.nth(i);
    const href = await link.getAttribute("href");
    if (href && href !== "/consultations" && !href.endsWith("/consultations")) {
      return { link, href };
    }
  }
  return null;
}

/**
 * Extracts the consultation ID from a consultation URL (either the current page
 * URL or an href), e.g. "/consultations/abc-123/..." -> "abc-123".
 */
export function getConsultationId(url: string): string | undefined {
  return url.match(/\/consultations\/([^/]+)/)?.[1];
}

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
