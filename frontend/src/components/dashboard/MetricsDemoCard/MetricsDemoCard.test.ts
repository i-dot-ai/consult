import { describe, expect, it, vi } from "vitest";
import { render } from "@testing-library/svelte";

import MetricsDemoCard from "./MetricsDemoCard.svelte";

describe("MetricsDemoCard", () => {
  const testData = {
    title: "Test Demo Card",
    items: [
      {
        title: "Test Demo Item 1",
        count: 5,
        percentage: 25,
      },
      {
        title: "Test Demo Item 2",
        count: 15,
        percentage: 75,
      },
    ],
    extraItems: [
      {
        title: "Test Demo Item 3",
        count: 5,
        percentage: 25,
      },
      {
        title: "Test Demo Item 4",
        count: 5,
        percentage: 25,
      },
      {
        title: "Test Demo Item 5",
        count: 5,
        percentage: 25,
      },
    ],
    hideThreshold: 3,
    consultationId: "123-456",
  };

  it("should render data", () => {
    const { getByText } = render(MetricsDemoCard, {
      title: testData.title,
      items: [...testData.items],
    });

    expect(getByText("Test Demo Card"));
    expect(getByText("Test Demo Item 1"));
    expect(getByText("25%"));

    expect(getByText("Test Demo Item 2"));
    expect(getByText(15));
    expect(getByText("75%"));
  });

  it("should hide items above max", async () => {
    vi.mock("svelte/transition");

    const { getByText, queryByText } = render(MetricsDemoCard, {
      ...testData,
      items: [...testData.items, ...testData.extraItems],
    });

    // Expect button label displays correct number of items
    expect(getByText("View All 5"));

    // Max display 3 initially
    expect(getByText("Test Demo Item 1"));
    expect(getByText("Test Demo Item 2"));
    expect(getByText("Test Demo Item 3"));
    expect(queryByText("Test Demo Item 4")).toBeNull();
    expect(queryByText("Test Demo Item 5")).toBeNull();
  });

  it("should not hide items if threshold is infinity", async () => {
    vi.mock("svelte/transition");

    const { getByText, queryByText } = render(MetricsDemoCard, {
      ...testData,
      items: [...testData.items, ...testData.extraItems],
      hideThreshold: Infinity,
    });

    // Expect button label displays correct number of items
    expect(queryByText("View All 5")).toBeNull();

    // Max display 3 initially
    expect(getByText("Test Demo Item 1"));
    expect(getByText("Test Demo Item 2"));
    expect(getByText("Test Demo Item 3"));
    expect(getByText("Test Demo Item 4"));
    expect(getByText("Test Demo Item 5"));
  });

  it("should format count display correctly", () => {
    const LONG_COUNT = 12345;

    const { getByText } = render(MetricsDemoCard, {
      title: testData.title,
      items: [
        {
          title: "Test Demo Item 1",
          count: LONG_COUNT,
          percentage: 100,
        },
      ],
    });

    expect(getByText("12,345"));
  });
});
