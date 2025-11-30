import { afterEach, describe, expect, it } from "vitest";
import { render } from "@testing-library/svelte";

import DemoFilter from "./DemoFilter.svelte";
import { getPercentage } from "../../global/utils";
import { demoFilters } from "../../global/state.svelte";

describe("DemoFilter", () => {
  const testData = {
    category: "country",
    demoOptions: { country: ["england", "scotland"] },
    demoData: { country: { england: 10, scotland: 20 } },
    totalCounts: { country: 30 },
  };

  afterEach(() => {
    demoFilters.reset();
  });

  it("should render data", () => {
    const { container, getByText } = render(DemoFilter, testData);

    expect(getByText("country")).toBeInTheDocument();

    Object.values(testData.demoData.country).forEach((value) => {
      expect(getByText(value)).toBeInTheDocument();
      const percentage = getPercentage(value, testData.totalCounts.country);
      expect(container.querySelector(`[title="${percentage}%"]`)).toBeTruthy();
    });
  });

  it("should not render data if skeleton", () => {
    const { container, queryByText } = render(DemoFilter, {
      ...testData,
      skeleton: true,
    });

    expect(queryByText("country")).toBeNull();

    Object.values(testData.demoData.country).forEach((value) => {
      expect(queryByText(value)).toBeNull();
      const percentage = getPercentage(value, testData.totalCounts.country);
      expect(container.querySelector(`[title="${percentage}%"]`)).toBeNull();
    });
  });

  // TODO: Update below case
  it.skip("should update filters state when clicked", async () => {
    const user = userEvent.setup();
    expect(demoFilters.filters).toEqual({});

    render(DemoFilter, {
      category: testData.category,
      demoOptions: testData.demoOptions,
      demoData: testData.demoData,
      totalCounts: testData.totalCounts,
    });

    const buttons = await screen.findAllByRole("button");

    for (const button of buttons) {
      await user.click(button);
    }

    expect(demoFilters.filters).toEqual(testData.demoOptions);
  });
});
