import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";

import HighlightedText from "./HighlightedText.svelte";

describe("HighlightedText", () => {
  it("should render plain text when highlight is empty", () => {
    render(HighlightedText, {
      text: "Hello world",
      highlight: "",
    });

    expect(screen.getByText("Hello world")).toBeInTheDocument();
    expect(screen.queryByTestId("highlighted-text")).not.toBeInTheDocument();
  });

  it("should handle text with no matches", () => {
    render(HighlightedText, {
      text: "Hello world",
      highlight: "xyz",
    });

    expect(screen.getByText("Hello world")).toBeInTheDocument();
    expect(screen.queryByTestId("highlighted-text")).not.toBeInTheDocument();
  });

  it("should highlight a single match", () => {
    render(HighlightedText, {
      text: "Hello world",
      highlight: "world",
    });

    expect(screen.getByText("Hello")).toBeInTheDocument();
    const highlightedText = screen.getByTestId("highlighted-text");
    expect(highlightedText).toBeInTheDocument();
    expect(highlightedText.textContent).toBe("world");
  });

  it("should highlight multiple matches", () => {
    render(HighlightedText, {
      text: "The cat and the dog",
      highlight: "the",
    });

    const highlightedTexts = screen.getAllByTestId("highlighted-text");
    expect(highlightedTexts.length).toBe(2);
    expect(highlightedTexts[0].textContent).toBe("The");
    expect(highlightedTexts[1].textContent).toBe("the");
  });
});
