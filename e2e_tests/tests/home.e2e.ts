import { test, expect } from "@playwright/test";


test.beforeEach(async({ page }) => {
  await page.goto("/");
})

test("get started link", async ({ page }) => {
  const getInvolvedButtons = await page
    .getByRole("link", { name: "Get involved" })
    .all();

  getInvolvedButtons.at(0)!.click();

  await expect(
    page.getByRole("heading", { name: "Get involved" }),
  ).toBeAttached();
});

test("has title", async ({ page }) => {
  await expect(page).toHaveTitle(/Consult/);
});

test("access cookie is set when page loads", async ({ page }) => {
  const cookies = await page.context().cookies();
  const accessCookie = cookies.find(cookie => cookie.name === "gdsInternalAccess");
  
  expect(accessCookie).toBeDefined();
});

test("displays support button", async ({ page }) => {
  const supportButton = page.getByLabel("Help and Support", { exact: true });
  expect(supportButton).toBeAttached();
});

test("support panel is initially hidden", async ({ page }) => {
  await expect(page.getByRole("heading", { name: "Help & Support" })).not.toBeAttached();
  await expect(page.getByRole("heading", { name: "Walkthrough" })).not.toBeAttached();
  await expect(page.getByRole("heading", { name: "Guidance" })).not.toBeAttached();
  await expect(page.getByRole("heading", { name: "Privacy notice" })).not.toBeAttached();
});

test("clicking support button reveals support panel", async ({ page }) => {
  const supportButton = page.getByLabel("Help and Support", { exact: true });
  await supportButton.click();

  await expect(page.getByRole("heading", { name: "Help & Support" })).toBeAttached({ timeout: 10000 });
  await expect(page.getByRole("heading", { name: "Walkthrough" })).toBeAttached();
  await expect(page.getByRole("heading", { name: "Guidance" })).toBeAttached();
  await expect(page.getByRole("heading", { name: "Privacy notice" })).toBeAttached();
});

test("clicking support button again hides support panel", async ({ page }) => {
  const supportButton = page.getByLabel("Help and Support", { exact: true });
  await supportButton.click();

  await expect(page.getByRole("heading", { name: "Help & Support", exact: true })).toBeAttached();

  await supportButton.click();

  await expect(page.getByText("Help & Support", {exact: true })).not.toBeAttached();
});
