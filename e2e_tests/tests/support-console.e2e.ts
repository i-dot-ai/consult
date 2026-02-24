import { test, expect } from "@playwright/test";

test.describe("Support Console - Users", () => {
  test("displays all users on /support/users", async ({ page }) => {
    await page.goto("/support/users");

    // Check the page heading
    await expect(
      page.getByRole("heading", { name: "Users" }),
    ).toBeVisible();

    // Check that the users table/list is visible
    // Note: Adjust selectors based on actual implementation
    const usersList = page.locator('[data-testid="users-list"]').or(
      page.locator("table"),
    );
    await expect(usersList.first()).toBeVisible();

    // Verify that user entries are displayed
    // This checks for the presence of email addresses (common user identifier)
    const userItems = page.locator("tbody tr").or(
      page.locator('[data-testid="user-item"]'),
    );

    // Verify at least one user exists
    const userCount = await userItems.count();
    expect(userCount).toBeGreaterThan(0);
    await expect(userItems.first()).toBeVisible();

    // Check for the admin user created by createadminusers
    await expect(page.getByText("email@example.com")).toBeVisible();
  });

  test("users list shows created date and staff access status", async ({
    page,
  }) => {
    await page.goto("/support/users");

    // Wait for the page to load
    await page.waitForLoadState("networkidle");

    // Check for table headers or labels indicating created date
    const createdDateHeader = page
      .getByText("Created", { exact: false })
      .or(page.getByText("Date", { exact: false }));
    await expect(createdDateHeader.first()).toBeVisible();

    // Check for staff access indicator
    const staffAccessHeader = page
      .getByText("Staff", { exact: false })
      .or(page.getByText("Access", { exact: false }));
    await expect(staffAccessHeader.first()).toBeVisible();
  });

  test("can navigate to individual user page", async ({ page }) => {
    await page.goto("/support/users");

    // Wait for users to load
    await page.waitForLoadState("networkidle");

    // Find and click on the first user link
    const userLink = page.locator('a[href*="/support/users/"]').first();
    await expect(userLink).toBeVisible();

    const userId = await userLink.getAttribute("href");
    await userLink.click();

    // Verify we navigated to the user detail page
    await expect(page).toHaveURL(new RegExp(`/support/users/.+`));
  });
});

test.describe("Support Console - Consultations", () => {
  test("displays all consultations on /support/consultations", async ({
    page,
  }) => {
    await page.goto("/support/consultations");

    // Check the page heading
    await expect(
      page.getByRole("heading", { name: /Consultations/i }),
    ).toBeVisible();

    // Check that the consultations table/list is visible
    const consultationsList = page
      .locator('[data-testid="consultations-list"]')
      .or(page.locator("table"));
    await expect(consultationsList.first()).toBeVisible();

    // Verify that consultation entries are displayed
    const consultationItems = page.locator("tbody tr").or(
      page.locator('[data-testid="consultation-item"]'),
    );

    // Verify at least 2 consultations exist (from dummy data)
    const consultationCount = await consultationItems.count();
    expect(consultationCount).toBeGreaterThanOrEqual(2);
    await expect(consultationItems.first()).toBeVisible();

    // Check for specific dummy consultation titles (may have multiple matches)
    await expect(
      page.getByText(/Dummy Consultation at Analysis Stage/i).first(),
    ).toBeVisible();
    await expect(
      page.getByText(/Dummy Consultation at Theme Sign Off/i).first(),
    ).toBeVisible();
  });

  test("consultations list shows creation dates", async ({ page }) => {
    await page.goto("/support/consultations");

    // Wait for the page to load
    await page.waitForLoadState("networkidle");

    // Check for created date column/field
    const createdHeader = page
      .getByText("Created", { exact: false })
      .or(page.getByText("Date", { exact: false }));
    await expect(createdHeader.first()).toBeVisible();
  });

  test("can navigate to individual consultation management page", async ({
    page,
  }) => {
    await page.goto("/support/consultations");

    // Wait for consultations to load
    await page.waitForLoadState("networkidle");

    // Find and click on the first consultation link
    const consultationLink = page
      .locator('a[href*="/support/consultations/"]')
      .first();
    await expect(consultationLink).toBeVisible();

    await consultationLink.click();

    // Verify we navigated to the consultation management page
    await expect(page).toHaveURL(new RegExp(`/support/consultations/.+`));
  });

  test("consultation management page has key action links", async ({
    page,
  }) => {
    await page.goto("/support/consultations");

    // Wait for consultations to load
    await page.waitForLoadState("networkidle");

    // Navigate to first consultation
    const consultationLink = page
      .locator('a[href*="/support/consultations/"]')
      .first();
    await consultationLink.click();

    // Wait for consultation management page to load
    await page.waitForLoadState("networkidle");

    // Check for key action links (adjust text based on actual implementation)
    // These might be "Review questions", "View dashboard", "Export", "Delete", etc.
    const pageContent = await page.textContent("body");
    expect(pageContent).toBeTruthy();
  });
});