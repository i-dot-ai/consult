import { describe, expect, it } from "vitest";
import { render } from "@testing-library/svelte";

import Title from "./Title.svelte";

describe("Title", () => {
  it("renders correct text", () => {
    const { getByText } = render(Title, {
      props: { text: "Test text" },
    });

    expect(getByText("Test text")).toBeInTheDocument();
  });

  it.each([1, 2, 3, 4, 5, 6])("renders correct tag", (level) => {
    const { container } = render(Title, {
      props: { level, text: "Test text" },
    });

    expect(container.querySelector(`h${level}`)).toBeTruthy();
  });
});
