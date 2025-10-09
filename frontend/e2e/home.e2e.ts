import { test, expect } from "@playwright/test";

test("get started link", async ({ page }) => {
  await page.goto("/");

  const getInvolvedButtons = await page
    .getByRole("link", { name: "Get involved" })
    .all();

  getInvolvedButtons.at(0)!.click();

  await expect(
    page.getByRole("heading", { name: "Get involved" }),
  ).toBeVisible();
});

test("has title", async ({ page }) => {
  await page.goto("/");

  await expect(page).toHaveTitle(/Consult/);
});
