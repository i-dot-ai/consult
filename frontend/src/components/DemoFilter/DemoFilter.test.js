import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { render, cleanup } from "@testing-library/svelte";

import DemoFilter from "./DemoFilter.svelte";
import { getPercentage } from "../../global/utils";
import { demoFilters } from "../../global/state.svelte";

let testData;

describe("DemoFilter", () => {
  beforeEach(() => {
    testData = {
      category: "country",
      demoOptions: { country: ["england", "scotland"] },
      demoData: { country: { england: 10, scotland: 20 } },
      totalCounts: { country: 30 },
    };

    demoFilters.reset();
  });

  afterEach(() => {
    cleanup();
    demoFilters.reset();
  });

  it("should render data", () => {
    const { container, getByText } = render(DemoFilter, {
      category: testData.category,
      demoOptions: testData.demoOptions,
      demoData: testData.demoData,
      totalCounts: testData.totalCounts,
    });

    expect(getByText(testData.category));
    Object.keys(testData.demoOptions).forEach((option) => {
      expect(getByText(option));

      Object.keys(testData.demoData[option]).forEach((rowKey) => {
        const rowValue = testData.demoData[option][rowKey];
        expect(getByText(rowValue));
        const percentage = getPercentage(
          rowValue,
          testData.totalCounts[option],
        );
        expect(
          container.querySelector(`[title="${percentage}%"]`),
        ).toBeTruthy();
      });
    });
  });

  it("should not render data if skeleton", () => {
    const { container, queryByText } = render(DemoFilter, {
      category: testData.category,
      demoOptions: testData.demoOptions,
      demoData: testData.demoData,
      totalCounts: testData.totalCounts,
      skeleton: true,
    });

    expect(queryByText(testData.category)).toBeNull();
    Object.keys(testData.demoOptions).forEach((option) => {
      expect(queryByText(option)).toBeNull();

      Object.keys(testData.demoData[option]).forEach((rowKey) => {
        const rowValue = testData.demoData[option][rowKey];
        expect(queryByText(rowValue)).toBeNull();
        const percentage = getPercentage(
          rowValue,
          testData.totalCounts[option],
        );
        expect(container.querySelector(`[title="${percentage}%"]`)).toBeNull();
      });
    });
  });

  // TODO: Update below case
  // it("should update filters state when clicked", async () => {
  //   vi.mock("svelte/transition");

  //   const user = userEvent.setup();
  //   expect(demoFilters.filters).toEqual({});

  //   render(DemoFilter, {
  //     category: testData.category,
  //     demoOptions: testData.demoOptions,
  //     demoData: testData.demoData,
  //     totalCounts: testData.totalCounts,
  //   });

  //   const buttons = await screen.findAllByRole("button");

  //   for (const button of buttons) {
  //     await user.click(button);
  //   }

  //   expect(demoFilters.filters).toEqual(testData.demoOptions);
  // });
});
