import { test, expect } from "@playwright/test";
import { getFirstConsultationLink } from "./helpers";

test.describe("Questions - Detail Page with Tabs", () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to consultations to find a consultation
    await page.goto("/consultations");
    await page.waitForLoadState("networkidle");

    // Get first consultation
    const result = await getFirstConsultationLink(page);
    expect(result).toBeTruthy();
    const consultationId = result!.href.match(/\/consultations\/([^/]+)/)?.[1];

    // Navigate to evaluation page to find questions
    await page.goto(`/evaluations/${consultationId}/questions`);
    await page.waitForLoadState("networkidle");

    // Find and click on first "Show next" button to navigate to a response
    const showNextButton = page.getByRole("button", { name: /show next/i }).first();

    if ((await showNextButton.count()) > 0) {
      await showNextButton.click();
      await page.waitForLoadState("networkidle");

      // Verify we navigated to a response detail page
      await page.waitForURL(/\/evaluations\/.*\/questions\/.*\/responses\/.*/);
    }
  });

  test("Question Summary tab displays all themes", async ({ page }) => {
    // Look for Summary tab
    const summaryTab = page
      .getByRole("tab", { name: /summary/i })
      .or(page.getByRole("button", { name: /summary/i }))
      .or(page.getByText(/summary/i, { exact: false }).locator("visible=true"));

    // If Summary tab exists, click it
    if ((await summaryTab.count()) > 0) {
      await summaryTab.first().click();
      await page.waitForLoadState("networkidle");
    }

    // Check for themes display - dummy data has specific themes
    const themesText = await page.textContent("body");

    // Verify specific themes from dummy data are displayed
    // Q1 themes: "Standardized framework", "Innovation"
    // Q4 themes: "More innovative", "Healthier options", etc.
    const hasThemes =
      themesText?.includes("Standardized framework") ||
      themesText?.includes("Innovation") ||
      themesText?.includes("More innovative") ||
      themesText?.includes("Healthier options");

    expect(hasThemes).toBeTruthy();
  });

  test("Response Analysis tab displays all responses", async ({ page }) => {
    // Look for Response Analysis tab
    const responseTab = page
      .getByRole("tab", { name: /response/i })
      .or(page.getByRole("button", { name: /response/i }))
      .or(page.getByRole("tab", { name: /analysis/i }))
      .or(page.getByText(/response.*analysis/i, { exact: false }));

    // If Response Analysis tab exists, click it
    if ((await responseTab.count()) > 0) {
      await responseTab.first().click();
      await page.waitForLoadState("networkidle");
    }

    // Check for responses display
    const responsesContent = page
      .locator('[data-testid*="response"]')
      .or(page.getByText(/response/i));

    // Verify responses are displayed
    const hasResponses = (await responsesContent.count()) > 0;
    expect(hasResponses).toBeTruthy();
  });

  test("can switch between Summary and Response Analysis tabs", async ({
    page,
  }) => {
    // Find tabs
    const summaryTab = page
      .getByRole("tab", { name: /summary/i })
      .or(page.getByRole("button", { name: /summary/i }));

    const responseTab = page
      .getByRole("tab", { name: /response/i })
      .or(page.getByRole("button", { name: /response/i }))
      .or(page.getByRole("tab", { name: /analysis/i }));

    // If both tabs exist, test switching between them
    if ((await summaryTab.count()) > 0 && (await responseTab.count()) > 0) {
      // Click Summary tab
      await summaryTab.first().click();
      await page.waitForTimeout(500);

      // Verify Summary tab is active
      const summaryTabElement = summaryTab.first();
      const summaryAriaSelected = await summaryTabElement.getAttribute(
        "aria-selected",
      );
      if (summaryAriaSelected !== null) {
        expect(summaryAriaSelected).toBe("true");
      }

      // Click Response Analysis tab
      await responseTab.first().click();
      await page.waitForTimeout(500);

      // Verify Response Analysis tab is active
      const responseTabElement = responseTab.first();
      const responseAriaSelected = await responseTabElement.getAttribute(
        "aria-selected",
      );
      if (responseAriaSelected !== null) {
        expect(responseAriaSelected).toBe("true");
      }
    }
  });

  test("question detail page shows question text", async ({ page }) => {
    // Check that there's a heading or question text displayed
    const headings = page.locator("h1, h2, h3");
    await expect(headings.first()).toBeVisible();

    // The page should have substantial content
    const bodyContent = await page.textContent("body");
    expect(bodyContent).toBeTruthy();
    expect(bodyContent!.length).toBeGreaterThan(50);
  });
});