import { describe, expect, it } from "vitest";
import { render } from "@testing-library/svelte";

import HighlightText from "./HighlightText.svelte";

describe("HighlightText", () => {
  it("wraps highlighted text inside span", () => {
    const { container } = render(HighlightText, {
      text: "Full test text",
      textToHighlight: "test",
    });

    const highlightedSpan = container.querySelector("span.bg-yellow-300");
    expect(highlightedSpan).toBeTruthy();
    expect(highlightedSpan?.textContent).toEqual("test");
  });

  it("handles upper and lower cases", () => {
    const { container } = render(HighlightText, {
      text: "full TeSt text",
      textToHighlight: "test",
    });

    const highlightedSpan = container.querySelector("span.bg-yellow-300");
    expect(highlightedSpan).toBeTruthy();
    expect(highlightedSpan?.textContent).toEqual("TeSt");
  });

  it("renders plain text when the text to highlight is empty", () => {
    const { container } = render(HighlightText, {
      text: "Full test text",
      textToHighlight: "",
    });

    expect(container.textContent).toBe("Full test text");
    expect(container.querySelector("span.bg-yellow-300")).toBeNull();
  });

  it("renders plain text when the text to highlight is not included in the text", () => {
    const { container } = render(HighlightText, {
      text: "Full test text",
      textToHighlight: "Not included in text",
    });

    expect(container.textContent).toBe("Full test text");
    expect(container.querySelector("span.bg-yellow-300")).toBeNull();
  });

  it("handles multiple matches", () => {
    const { container } = render(HighlightText, {
      text: "test this test again",
      textToHighlight: "test",
    });

    const highlightedSpans = container.querySelectorAll("span.bg-yellow-300");
    expect(highlightedSpans).toHaveLength(2);
    expect(highlightedSpans[0]?.textContent).toEqual("test");
    expect(highlightedSpans[1]?.textContent).toEqual("test");
  });
});
