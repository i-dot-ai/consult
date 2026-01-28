import { test, expect } from "@playwright/test";


const HEADINGS = [
  "Guidance",
  "Set up data - Human step",
  "Find themes - AI process",
  "Finalise themes - Human step",
  "Assign themes - AI process",
  "Check quality - Human step",
  "Real-time mapping evaluation - done for all consultations",
  "Prospective mapping evaluation",
  "Analyse - Human step",
  "Consult Does",
  "Consult Does Not"
];

const URLS = [
  "https://ai.gov.uk/evaluations/consult-evaluation-dwp-s-pathways-to-work-consultation/",
  "https://ai.gov.uk/evaluations/consult-evaluation-independent-water-commission-call-for-evidence/",
  "https://ai.gov.uk/docs/Scot_Gov_NSCP_Evaluation_Report.pdf",
  "https://github.com/i-dot-ai/themefinder/blob/main/src/themefinder/prompts/detail_detection.txt",
  "https://github.com/i-dot-ai/themefinder/blob/main/src/themefinder/prompts/theme_mapping.txt",
  "https://github.com/i-dot-ai/themefinder/blob/main/src/themefinder/prompts/theme_generation.txt",
  "https://github.com/i-dot-ai/themefinder/blob/main/src/themefinder/prompts/theme_condensation.txt",
  "https://github.com/i-dot-ai/themefinder/blob/main/src/themefinder/prompts/theme_refinement.txt",
  "https://github.com/i-dot-ai/themefinder/blob/main/src/themefinder/prompts/agentic_theme_clustering.txt",
]

test("displays guidance heading", async ({ page }) => {
  await page.goto("/guidance");

  HEADINGS.forEach(async heading => {  
    await expect(page.getByRole("heading", { name: heading, exact: true })).toBeVisible();
  })
});

test("displays links with correct urls", async ({ page }) => {
  await page.goto("/guidance");
  URLS.forEach(async url => {
    await expect(page.locator(`a[href="${url}"]`)).toBeVisible();
  })
});
