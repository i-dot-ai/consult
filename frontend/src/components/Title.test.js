import { describe, expect, it } from "vitest";
import { render } from "@testing-library/svelte";

import Title from "./Title.svelte";

describe("Title", () => {
  it("renders correct text", () => {
    const text = "Test Text";
    const level = 1;
    const { getByText } = render(Title, {
      props: { level: level, text: text },
    });

    expect(getByText(text));
  });
  it.each([1, 2, 3, 4, 5, 6])("renders correct tag", (level) => {
    const text = "Test Text";
    const { container } = render(Title, {
      props: { level: level, text: text },
    });

    expect(container.querySelector(`h${level}`)).toBeTruthy();
  });
  it.each([0, 7, -1])("throws if invalid level", (level) => {
    const text = "Test Text";
    expect(render(Title, { props: { level: level, text: text } }).toThrow);
  });
});
