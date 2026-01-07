import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";

import FloatingPanelContent from "./FloatingPanelContent.svelte";

describe("FloatingPanelContent", () => {
  it.each(["Walkthrough", "Guidance", "Feedback", "Privacy notice"])("renders titles", (itemText) => {
    render(FloatingPanelContent);

    expect(screen.getByText(itemText)).toBeInTheDocument();
  });

  it.each([
    "Interactive tutorial for Theme Sign Off",
    "View help documentation",
    "Send us your feedback",
    "View our privacy policy",
  ])("renders subtitles", (itemText) => {
    render(FloatingPanelContent);

    expect(screen.getByText(itemText)).toBeInTheDocument();
  });

  it("matches snapshot", () => {
    const { container } = render(FloatingPanelContent);

    expect(container).toMatchSnapshot();
  });
});
