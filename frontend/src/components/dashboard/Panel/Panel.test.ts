import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";

import { createRawSnippet } from "svelte";

import Panel from "./Panel.svelte";
import PanelStory from "./PanelStory.svelte";

describe("Panel", () => {
  const childComponent = createRawSnippet(() => {
    return {
      render: () => "<p>Child Content</p>",
    };
  });

  it("should render slot", () => {
    render(Panel, { children: childComponent });

    expect(screen.getByText("Child Content")).toBeInTheDocument();
  });

  it("should render correct css based on props", () => {
    render(Panel, {
      border: true,
      bg: true,
      children: childComponent,
    });

    const panel = screen.getByTestId("panel-component");
    expect(panel.getAttribute("class")).toContain("border");
    expect(panel.getAttribute("class")).toContain("bg-");
  });

  it("should have a story configured correctly", () => {
    expect(PanelStory).toHaveProperty("name", "Panel");
    expect(PanelStory).toHaveProperty("component", Panel);
    expect(PanelStory).toHaveProperty("props");

    const propsDefined = PanelStory.props.map(prop => prop.name);
    expect(propsDefined).toEqual([
      "variant",
      "border",
      "bg",
      "level",
      "children",
    ])
  })
});
