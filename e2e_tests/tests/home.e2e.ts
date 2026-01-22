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
  ).toBeVisible();
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
  const supportButton = page.getByLabel("Help and Support");
  expect(supportButton).toBeVisible();
});

test("support panel is initially hidden", async ({ page }) => {
  await expect(page.getByRole("heading", { name: "Help & Support" })).not.toBeVisible();
  await expect(page.getByRole("heading", { name: "Walkthrough" })).not.toBeVisible();
  await expect(page.getByRole("heading", { name: "Guidance" })).not.toBeVisible();
  await expect(page.getByRole("heading", { name: "Privacy notice" })).not.toBeVisible();
});

test("clicking support button reveals support panel", async ({ page }) => {
  const supportButton = page.getByLabel("Help and Support");
  await supportButton.click();

  await expect(page.getByRole("heading", { name: "Help & Support" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Walkthrough" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Guidance" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Privacy notice" })).toBeVisible();
});
