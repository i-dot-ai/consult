import type { Page } from "@playwright/test";

/**
 * Finds the first consultation link that points to an actual consultation detail page
 * (not the consultations list page itself)
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