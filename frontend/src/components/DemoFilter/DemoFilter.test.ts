import { afterEach, describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";

import DemoFilter from "./DemoFilter.svelte";
import { getPercentage } from "../../global/utils";
import { demoFilters } from "../../global/state.svelte";
import userEvent from "@testing-library/user-event";
import DemoFilterStory from "./DemoFilterStory.svelte";

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
    render(DemoFilter, testData);

    expect(screen.getByText("country")).toBeInTheDocument();

    Object.values(testData.demoData.country).forEach((value) => {
      expect(screen.getByText(value)).toBeInTheDocument();
      const percentage = getPercentage(value, testData.totalCounts.country);
      expect(screen.getByTitle(`${percentage}%`)).toBeInTheDocument();
    });
  });

  it("should not render data title if skeleton", () => {
    render(DemoFilter, {
      ...testData,
      skeleton: true,
    });

    expect(screen.queryByText("country")).toBeNull();
  });

  it.each(Object.values(testData.demoData.country))(
    "should not render data content if skeleton",
    (value) => {
      render(DemoFilter, {
        ...testData,
        skeleton: true,
      });

      expect(screen.queryByText(value)).not.toBeInTheDocument();
      const percentage = getPercentage(value, testData.totalCounts.country);
      expect(screen.queryByTitle(`${percentage}%`)).not.toBeInTheDocument();
    },
  );

  // TODO: Update below case
  it.todo("should update filters state when clicked", async () => {
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

  it("should have a story configured correctly", () => {
    expect(DemoFilterStory).toHaveProperty("name", "DemoFilter");
    expect(DemoFilterStory).toHaveProperty("component", DemoFilter);
    expect(DemoFilterStory).toHaveProperty("props");

    const propsDefined = DemoFilterStory.props.map((prop) => prop.name);
    expect(propsDefined).toEqual([
      "category",
      "demoOptions",
      "demoData",
      "totalCounts",
      "skeleton",
    ]);
  });
});
