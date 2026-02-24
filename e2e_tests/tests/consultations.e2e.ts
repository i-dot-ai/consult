import { test, expect } from "@playwright/test";

test.describe("Consultations - List Page", () => {
  test("displays consultations user has been added to", async ({ page }) => {
    await page.goto("/consultations");

    // Check the page heading
    await expect(
      page.getByRole("heading", { name: /Your consultations/i }),
    ).toBeVisible();

    // Check for the description text
    await expect(
      page.getByText(/review themes/i),
    ).toBeVisible();

    // Wait for consultations to load
    await page.waitForLoadState("networkidle");

    // Check that at least one consultation is displayed
    const consultationItems = page
      .locator('[data-testid="consultation-item"]')
      .or(page.locator("article"))
      .or(page.locator('a[href*="/consultations/"]'));

    // Verify at least one consultation exists
    const count = await consultationItems.count();
    expect(count).toBeGreaterThan(0);
    await expect(consultationItems.first()).toBeVisible();

    // Check for the specific dummy consultations (may have multiple matches)
    await expect(
      page.getByText(/Dummy Consultation at Analysis Stage/i).first(),
    ).toBeVisible();
    await expect(
      page.getByText(/Dummy Consultation at Theme Sign Off/i).first(),
    ).toBeVisible();
  });

  test("can navigate to a consultation detail page", async ({ page }) => {
    await page.goto("/consultations");

    // Wait for consultations to load
    await page.waitForLoadState("networkidle");

    // Find all consultation links
    const allLinks = page.locator('a[href*="/consultations/"]');
    const count = await allLinks.count();

    // Find first link that's not exactly /consultations
    let consultationLink = null;
    for (let i = 0; i < count; i++) {
      const link = allLinks.nth(i);
      const href = await link.getAttribute("href");
      if (href && href !== "/consultations" && !href.endsWith("/consultations")) {
        consultationLink = link;
        break;
      }
    }

    expect(consultationLink).toBeTruthy();
    await consultationLink!.click();

    // Verify we navigated to a consultation detail page (could be root or a subpage)
    await expect(page).toHaveURL(new RegExp(`/consultations/[^/]+`));
  });
});

test.describe("Consultations - Detail/Dashboard Page", () => {
  test("consultation dashboard displays key metrics and questions", async ({
    page,
  }) => {
    await page.goto("/consultations");
    await page.waitForLoadState("networkidle");

    // Navigate to first consultation
    const allLinks = page.locator('a[href*="/consultations/"]');
    const count = await allLinks.count();

    let consultationLink = null;
    for (let i = 0; i < count; i++) {
      const link = allLinks.nth(i);
      const href = await link.getAttribute("href");
      if (href && href !== "/consultations" && !href.endsWith("/consultations")) {
        consultationLink = link;
        break;
      }
    }

    expect(consultationLink).toBeTruthy();
    await consultationLink!.click();

    await page.waitForLoadState("networkidle");

    // Check for key dashboard elements
    // 1. Search functionality should be present
    const searchInput = page.locator("#search-input");
    await expect(searchInput).toBeVisible();

    // 2. Section headings should be present
    await expect(
      page.getByRole("heading", { name: /All consultation questions/i }),
    ).toBeVisible();

    // 3. Question cards should be displayed - dummy data has 4 questions per consultation
    const questionCards = page.locator('[data-testid="question-icon"]');
    const questionCount = await questionCards.count();
    expect(questionCount).toBeGreaterThanOrEqual(4);

    // 4. Check for metrics section showing questions
    const metricsText = await page.textContent("body");
    expect(metricsText).toMatch(/\d+ questions?/);

    // 5. Check for specific question text from dummy data
    await expect(
      page.getByText(/chocolate bar regulations/i),
    ).toBeVisible();

    // 6. Check for response counts (each question has 100 responses)
    await expect(page.getByText(/100 responses/i).first()).toBeVisible();
  });

  test("can navigate to evaluation page from consultation", async ({
    page,
  }) => {
    await page.goto("/consultations");
    await page.waitForLoadState("networkidle");

    // Navigate to first consultation
    const allLinks = page.locator('a[href*="/consultations/"]');
    const count = await allLinks.count();

    let consultationLink = null;
    let consultationUrl = null;
    for (let i = 0; i < count; i++) {
      const link = allLinks.nth(i);
      const href = await link.getAttribute("href");
      if (href && href !== "/consultations" && !href.endsWith("/consultations")) {
        consultationLink = link;
        consultationUrl = href;
        break;
      }
    }

    expect(consultationLink).toBeTruthy();
    await consultationLink!.click();

    await page.waitForLoadState("networkidle");

    // Extract consultation ID from URL
    const consultationId = consultationUrl?.match(/\/consultations\/([^/]+)/)?.[1];
    expect(consultationId).toBeTruthy();

    // Look for a link to the evaluation page
    const evalLink = page
      .locator(`a[href*="/evaluations/${consultationId}/questions"]`)
      .or(page.getByRole("link", { name: /questions/i }))
      .or(page.getByRole("link", { name: /evaluation/i }));

    // If the link exists, click it
    if ((await evalLink.count()) > 0) {
      await evalLink.first().click();
      await expect(page).toHaveURL(
        new RegExp(`/evaluations/${consultationId}/questions`),
      );
    }
  });
});

test.describe("Consultations - Evaluation Page", () => {
  test("evaluation page displays all questions", async ({ page }) => {
    // First navigate to consultations list
    await page.goto("/consultations");
    await page.waitForLoadState("networkidle");

    // Get first consultation
    const allLinks = page.locator('a[href*="/consultations/"]');
    const count = await allLinks.count();

    let consultationUrl = null;
    for (let i = 0; i < count; i++) {
      const link = allLinks.nth(i);
      const href = await link.getAttribute("href");
      if (href && href !== "/consultations" && !href.endsWith("/consultations")) {
        consultationUrl = href;
        break;
      }
    }

    expect(consultationUrl).toBeTruthy();
    const consultationId = consultationUrl?.match(/\/consultations\/([^/]+)/)?.[1];

    // Navigate directly to evaluation page
    await page.goto(`/evaluations/${consultationId}/questions`);
    await page.waitForLoadState("networkidle");

    // Verify we're on the evaluation page
    await expect(page).toHaveURL(new RegExp(`/evaluations/.+/questions`));

    // Check for the page heading
    await expect(
      page.getByRole("heading", { name: /free text questions/i }),
    ).toBeVisible();

    // Check that the form with questions exists
    const form = page.locator("form");
    await expect(form).toBeVisible();

    // Check for "Show next" buttons - dummy data has 2 free text questions (Q1 and Q4)
    const showNextButtons = page.getByRole("button", { name: /show next/i });
    const buttonCount = await showNextButtons.count();
    expect(buttonCount).toBeGreaterThanOrEqual(2);

    // Check for specific question text
    await expect(
      page.getByText(/chocolate bar regulations/i).first(),
    ).toBeVisible();

    // Check for percentage reviewed text
    await expect(page.getByText(/reviewed/i).first()).toBeVisible();
  });

  test("can click on a question from evaluation page", async ({ page }) => {
    // Navigate to consultations
    await page.goto("/consultations");
    await page.waitForLoadState("networkidle");

    // Get first consultation
    const allLinks = page.locator('a[href*="/consultations/"]');
    const count = await allLinks.count();

    let consultationUrl = null;
    for (let i = 0; i < count; i++) {
      const link = allLinks.nth(i);
      const href = await link.getAttribute("href");
      if (href && href !== "/consultations" && !href.endsWith("/consultations")) {
        consultationUrl = href;
        break;
      }
    }

    expect(consultationUrl).toBeTruthy();
    const consultationId = consultationUrl?.match(/\/consultations\/([^/]+)/)?.[1];

    // Navigate to evaluation page
    await page.goto(`/evaluations/${consultationId}/questions`);
    await page.waitForLoadState("networkidle");

    // Find and click on first question link
    const questionLink = page
      .locator('a[href*="/responses/"]')
      .or(page.locator('a[href*="/questions/"]'))
      .first();

    if ((await questionLink.count()) > 0) {
      await questionLink.click();

      // Should navigate to a question detail page
      await expect(page).toHaveURL(
        new RegExp(`/(consultations|evaluations)/.+/(responses|questions)/.+`),
      );
    }
  });
});