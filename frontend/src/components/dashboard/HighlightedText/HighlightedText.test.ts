import { describe, expect, it } from "vitest";
import { render } from "@testing-library/svelte";

import HighlightedText from "./HighlightedText.svelte";

describe("HighlightedText", () => {
  it("should render plain text when highlight is empty", () => {
    const { container } = render(HighlightedText, {
      text: "Hello world",
      highlight: "",
    });

    expect(container.textContent).toBe("Hello world");
    expect(container.querySelector("span.bg-yellow-300")).toBeFalsy();
  });

  it("should handle empty text", () => {
    const { container } = render(HighlightedText, {
      text: "",
      highlight: "test",
    });

    expect(container.textContent).toBe("");
  });

  it("should handle text with no matches", () => {
    const { container } = render(HighlightedText, {
      text: "Hello world",
      highlight: "xyz",
    });

    expect(container.textContent).toBe("Hello world");
    expect(container.querySelector("span.bg-yellow-300")).toBeFalsy();
  });

  it("should highlight a single match", () => {
    const { container } = render(HighlightedText, {
      text: "Hello world",
      highlight: "world",
    });

    expect(container.textContent).toBe("Hello world");
    const highlightedSpan = container.querySelector("span.bg-yellow-300");
    expect(highlightedSpan).toBeTruthy();
    expect(highlightedSpan?.textContent).toBe("world");
  });

  it("should highlight multiple matches", () => {
    const { container } = render(HighlightedText, {
      text: "The cat and the dog",
      highlight: "the",
    });

    const highlightedSpans = container.querySelectorAll("span.bg-yellow-300");
    expect(highlightedSpans.length).toBe(2);
    expect(highlightedSpans[0].textContent).toBe("The");
    expect(highlightedSpans[1].textContent).toBe("the");
  });
});
