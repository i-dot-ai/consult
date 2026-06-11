import { test, expect } from '@playwright/test';
import type { Page } from '@playwright/test';
import { setTimeout } from 'timers/promises';

import {
  createFixtureData,
  deleteFixtureData,
  goToQuestion,
} from './helpers';
import { analysisConsultation } from '../fixtures';
import type { FixtureReference } from '../fixtures';

function sleep() {
  return setTimeout(1000);
}

const freeTextResponses = (page: Page) =>
  page
    .locator('section')
    .filter({ has: page.getByRole('heading', { name: 'Free Text Responses' }) })
    .locator('ul li');

function getFilterButton(
  page: Page,
  containerSelector: string,
  filter: string,
  labelSelector?: string,
) {
  if (labelSelector) {
    return page
      .locator(containerSelector)
      .locator('button, [role="button"]')
      .filter({ has: page.locator(labelSelector).filter({ hasText: new RegExp(`^${filter}$`) }) });
  }
  return page.locator(containerSelector).getByRole('button', { name: new RegExp(`^${filter}`) });
}

async function testFilter(
  page: Page,
  filterNames: string[],
  sameGroupFilters: string[],
  totalCount: number,
  {
    operator = 'OR',
    countSelector = 'span.text-right',
    containerSelector = 'aside',
    labelSelector,
  }: {
    operator?: 'AND' | 'OR';
    countSelector?: string;
    containerSelector?: string;
    labelSelector?: string;
  } = {},
) {
  const expectedCounts = [];

  // AND option only allowed for max two filters (one in each group)
  if (operator === 'AND' && filterNames.length != 2) {
    throw new Error('AND operator only supported for two filters');
  }

  // When we click multiple filters in the same group an unclicked filter will show zero before clicking and
  // then the true value after clicking - so we need to get the expected count for each filter before clicking any of them
  for (const filter of filterNames) {
    const filterButton = getFilterButton(page, containerSelector, filter, labelSelector);

    const countText = await filterButton.locator(countSelector).textContent();
    expectedCounts.push(parseInt(countText!.trim()));
  }

  // Now click each filter in turn and check count is correct after each click (should be same as before clicking)
  for (const [i, filter] of filterNames.entries()) {
    const filterButton = getFilterButton(page, containerSelector, filter, labelSelector);

    // For AND we do need to update expected counts for second filter as the value will change after
    // first filter is applied. For OR our previous expected counts should not be affected.
    if (operator === 'AND' && i === 1) {
      expectedCounts[1] = await filterButton
        .locator(countSelector)
        .textContent()
        .then((text) => parseInt(text!.trim()));
    }

    await filterButton.click();
    await page.waitForLoadState('networkidle');

    // Check filter still shows correct count after click (should be same as before)
    await sleep(); // Wait for any debounce to finish and count to update
    const newCountText = await filterButton.locator(countSelector).textContent();
    expect(parseInt(newCountText!.trim())).toBe(expectedCounts[i]);
  }

  // Response list should show only matching responses
  if (operator === 'AND') {
    // For AND, count should be same as last filter clicked (most specific)
    await expect(freeTextResponses(page)).toHaveCount(expectedCounts.at(-1)!);
  }
  else if (operator === 'OR') {
    // For OR, count should be sum of all selected filters (no overlap in our test data so just sum)
    await expect(freeTextResponses(page)).toHaveCount(expectedCounts.reduce((a, b) => a + b, 0));
  }

  // All other filters in the same group should show 0
  for (const other of sameGroupFilters) {
    if (filterNames.includes(other)) continue; // Skip the filters we selected
    const otherCountText = await getFilterButton(page, containerSelector, other, labelSelector)
      .locator(countSelector)
      .textContent();
    expect(parseInt(otherCountText!.trim())).toBe(0);
  }

  // Reset and confirm full list is restored
  for (const filter of filterNames) {
    await getFilterButton(page, containerSelector, filter, labelSelector).click();
    await page.waitForLoadState('networkidle');
    await sleep(); // Wait for any debounce to finish and count to update
  }
  await expect(freeTextResponses(page)).toHaveCount(totalCount);
}

test.describe('Response Analysis Page', () => {
  let testData: FixtureReference = {};

  test.beforeAll(async ({ request }) => {
    testData = await createFixtureData(request, {
      consultations: [analysisConsultation],
    });
  });

  test.beforeEach(async ({ page }) => {
    await goToQuestion(page, testData.consultation_ids![0], testData.question_ids![0]);
  });

  test('demographic filters show correct response counts', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /Filters/i })).toBeVisible();

    const totalCount = await freeTextResponses(page).count();

    const nationFilters = ['England', 'Wales', 'Scotland', 'Northern Ireland'];
    const ageGroupFilters = ['18-35', '36-50', '51-65'];

    for (const filter of nationFilters) {
      await testFilter(page, [filter], nationFilters, totalCount);
    }
    for (const filter of ageGroupFilters) {
      await testFilter(page, [filter], ageGroupFilters, totalCount);
    }

    // Check two filters in same group (e.g. England + Wales) - should show responses matching either filter
    await testFilter(page, ['England', 'Wales'], nationFilters, totalCount);

    // Check combined filters (e.g. England + 18-35) - should show only responses matching both
    await testFilter(page, ['England', '18-35'], [...nationFilters, ...ageGroupFilters], totalCount, {
      operator: 'AND',
    });
  });

  test('filters on categorical question show correct response counts', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /Multiple Choice Answers/i })).toBeVisible();

    const totalCount = await freeTextResponses(page).count();
    const options = ['Yes', 'No', "Don't know", 'No answer'];

    for (const option of options) {
      // Multichoice options may be overlapping so we cannot assume that other options will be zero
      await testFilter(page, [option], [], totalCount, {
        countSelector: 'span[class~="sm:hidden"]',
        containerSelector: 'section:has-text("Multiple Choice Answers")',
        labelSelector: 'h3',
      });
    }
  });

  test('select theme filters show correct response counts', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /Theme analysis/i })).toBeVisible();

    const totalCount = await freeTextResponses(page).count();
    const themes = ['Standardized framework', 'Innovation'];

    for (const theme of themes) {
      // Theme filters may be overlapping so we cannot assume that other themes will be zero
      await testFilter(page, [theme], [], totalCount, {
        containerSelector: 'section:has-text("Theme analysis") table',
        countSelector: 'td:nth-child(2)',
      });
    }
  });

  test('flagged toggle shows only flagged responses', async ({ page }) => {
    // Flag the first response
    await freeTextResponses(page).first().getByTitle('Flag response').click();
    await page.waitForLoadState('networkidle');

    // Enable the flagged-only toggle
    await page.getByRole('switch', { name: /Flagged/i }).click();
    await page.waitForLoadState('networkidle');

    // Only the flagged response should be visible
    await expect(freeTextResponses(page)).toHaveCount(1);

    // Unflag to clean up, then disable toggle
    await freeTextResponses(page).first().getByTitle('Flag response').click();
    await page.waitForLoadState('networkidle');
    await page.getByRole('switch', { name: /Flagged/i }).click();
    await page.waitForLoadState('networkidle');
  });

  test('click respondent goes to respondent details page', async ({ page }) => {
    // Click the respondent button on the first response
    const firstResponse = freeTextResponses(page).first();
    await firstResponse.getByTestId('respondent-button').click();

    // Should navigate to the respondent detail page
    await page.waitForURL(/\/respondent\/\d+/);
    await expect(page.getByText(new RegExp(`Respondent\\s*\\d+`))).toBeVisible();
  });

  test.afterAll(async () => {
    await deleteFixtureData(testData);
  });
});
