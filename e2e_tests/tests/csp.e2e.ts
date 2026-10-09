import { test, expect, type Page } from "@playwright/test";

import { CleanupManager, createFixtureData } from "./helpers";
import { gotoFinaliseThemesList } from "./navigation";
import { signOffConsultation } from "../fixtures";
import type { FixtureReference } from "../fixtures";

// Must be registered before the first navigation, or early violations are missed.
async function trackCspViolations(page: Page): Promise<string[]> {
  const violations: string[] = [];
  await page.exposeFunction("reportCspViolation", (entry: string) => {
    violations.push(entry);
  });
  await page.addInitScript(() => {
    document.addEventListener("securitypolicyviolation", (event) => {
      const report = window as unknown as {
        reportCspViolation: (entry: string) => void;
      };
      report.reportCspViolation(
        `${event.violatedDirective} ${event.blockedURI}`,
      );
    });
  });
  return violations;
}

test("CSP forbids unsafe-inline for scripts and styles", async ({ page }) => {
  const violations = await trackCspViolations(page);

  // Astro serves CSP as a response header (not a meta tag) for on-demand pages.
  const response = await page.goto("/");
  const content = response?.headers()["content-security-policy"];

  expect(
    content,
    "CSP response header should be present in the built app",
  ).toBeTruthy();

  const directives = new Map(
    content!.split(";").map((directive) => {
      const [name, ...values] = directive.trim().split(/\s+/);
      return [name, values];
    }),
  );

  for (const [name, values] of directives) {
    if (name.startsWith("script-src") || name.startsWith("style-src")) {
      expect(values, `${name} must not allow unsafe-inline`).not.toContain(
        "'unsafe-inline'",
      );
    }
  }

  expect(violations, "no CSP violations should fire on load").toEqual([]);
});

test("floating help panel opens with no CSP violations", async ({ page }) => {
  const violations = await trackCspViolations(page);

  await page.goto("/");

  // melt positions the open panel through the CSSOM; an inline style attr would trip style-src.
  await page.locator(".floating-panel").getByRole("button").click();
  await expect(
    page.getByRole("heading", { name: "Help & Support" }),
  ).toBeVisible();

  expect(violations).toEqual([]);
});

test.describe("CSP leaves refactored components intact", () => {
  test.describe.configure({ mode: "serial" });

  const cleanupManager = new CleanupManager();
  let testData: FixtureReference = {};

  test.beforeAll(async ({ request }) => {
    testData = await createFixtureData(request, {
      consultations: [signOffConsultation],
    });
    cleanupManager.add(testData);
  });

  test.afterAll(async () => {
    await cleanupManager.cleanup();
  });

  test("onboarding tour fires no CSP violations", async ({ page }) => {
    const violations = await trackCspViolations(page);

    await gotoFinaliseThemesList(page, signOffConsultation.title, {
      dismissOnboarding: false,
    });
    await expect(
      page.getByRole("heading", { name: "Welcome to Finalise Themes" }),
    ).toBeVisible();
    await page.getByRole("button", { name: "Get Started" }).click();

    expect(violations).toEqual([]);
  });

  test("theme cards and theme textarea fire no CSP violations", async ({
    page,
  }) => {
    const violations = await trackCspViolations(page);

    await gotoFinaliseThemesList(page, signOffConsultation.title);

    const freeTextQuestion = signOffConsultation.questions!.find(
      (question) => question.has_free_text,
    )!;
    await page
      .getByTestId("question-card")
      .filter({ hasText: freeTextQuestion.text })
      .click();
    await page.waitForLoadState("networkidle");

    await page.getByRole("button", { name: "Add Custom Theme" }).click();
    await expect(page.getByLabel("Theme Description")).toBeVisible();

    expect(violations).toEqual([]);
  });
});
