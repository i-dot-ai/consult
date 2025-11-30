import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";

import { createRawSnippet } from "svelte";

import Panel from "./Panel.svelte";

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
});
