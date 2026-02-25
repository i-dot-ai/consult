import type { Page } from "@playwright/test";

/**
 * Finds the first consultation link that points to an actual consultation detail page
 * (not the consultations list page itself)
 */
export async function getFirstConsultationLink(page: Page) {
  const allLinks = page.locator('a[href*="/consultations/"]');
  const count = await allLinks.count();

  // Get all hrefs and find the first valid one
  const hrefs = await Promise.all(
    Array.from({ length: count }, (_, i) => allLinks.nth(i).getAttribute("href"))
  );

  const validHref = hrefs.find(
    (href) => href && href !== "/consultations" && !href.endsWith("/consultations")
  );

  if (!validHref) {
    return null;
  }

  // Return the link element and href for the valid consultation
  return {
    link: page.locator(`a[href="${validHref}"]`).first(),
    href: validHref,
  };
}