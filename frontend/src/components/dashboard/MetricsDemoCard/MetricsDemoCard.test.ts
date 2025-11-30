import { describe, expect, it } from "vitest";
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

    expect(getByText("Test Demo Card")).toBeInTheDocument();
    expect(getByText("Test Demo Item 1")).toBeInTheDocument();
    expect(getByText("25%")).toBeInTheDocument();

    expect(getByText("Test Demo Item 2")).toBeInTheDocument();
    expect(getByText(15)).toBeInTheDocument();
    expect(getByText("75%")).toBeInTheDocument();
  });

  it("should hide items above max", async () => {
    const { getByText, queryByText } = render(MetricsDemoCard, {
      ...testData,
      items: [...testData.items, ...testData.extraItems],
    });

    // Expect button label displays correct number of items
    expect(getByText("View All 5")).toBeInTheDocument();

    // Max display 3 initially
    expect(getByText("Test Demo Item 1")).toBeInTheDocument();
    expect(getByText("Test Demo Item 2")).toBeInTheDocument();
    expect(getByText("Test Demo Item 3")).toBeInTheDocument();
    expect(queryByText("Test Demo Item 4")).toBeNull();
    expect(queryByText("Test Demo Item 5")).toBeNull();
  });

  it("should not hide items if threshold is infinity", async () => {
    const { getByText, queryByText } = render(MetricsDemoCard, {
      ...testData,
      items: [...testData.items, ...testData.extraItems],
      hideThreshold: Infinity,
    });

    // Expect button label displays correct number of items
    expect(queryByText("View All 5")).toBeNull();

    // Max display 3 initially
    expect(getByText("Test Demo Item 1")).toBeInTheDocument();
    expect(getByText("Test Demo Item 2")).toBeInTheDocument();
    expect(getByText("Test Demo Item 3")).toBeInTheDocument();
    expect(getByText("Test Demo Item 4")).toBeInTheDocument();
    expect(getByText("Test Demo Item 5")).toBeInTheDocument();
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

    expect(getByText("12,345")).toBeInTheDocument();
  });
});
