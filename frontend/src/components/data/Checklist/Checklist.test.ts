import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/svelte";

import Checklist from "./Checklist.svelte";
import { TEST_DATA } from "./testData";

describe("Checklist", () => {
  const testData = { items: TEST_DATA.items, onChange: vi.fn() };

  it.each(testData.items)("should render title", (item) => {
    render(Checklist, testData);

    expect(screen.getByText(item.title)).toBeInTheDocument();
  });

  it.each(testData.items)("should render text", (item) => {
    render(Checklist, testData);

    expect(screen.getByText(item.text)).toBeInTheDocument();
  });

  it.each(testData.items)("should render id", (item) => {
    const { container } = render(Checklist, testData);

    expect(
      // eslint-disable-next-line testing-library/no-container
      container.querySelector(`#checklist-${item.id}`),
    ).toBeInTheDocument();
  });
});
