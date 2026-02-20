import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";

import Checklist from "./Checklist.svelte";
import { TEST_DATA } from "./testData";

describe("Checklist", () => {
  const testData = { items: TEST_DATA.items };

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

    expect(container.querySelector(`#checklist-${item.id}`)).toBeInTheDocument();
  });
});
