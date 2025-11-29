import { describe, expect, it } from "vitest";
import { render } from "@testing-library/svelte";

import { createRawSnippet } from "svelte";

import Panel from "./Panel.svelte";

describe("Panel", () => {
  const childComponent = createRawSnippet(() => {
    return {
      render: () => "<p>Child Content</p>",
    };
  });

  it("should render slot", () => {
    const { getByText } = render(Panel, { children: childComponent });

    expect(getByText("Child Content"));
  });

  it("should render correct css based on props", () => {
    const { getByTestId } = render(Panel, {
      border: true,
      bg: true,
      children: childComponent,
    });

    const panel = getByTestId("panel-component");
    expect(panel.getAttribute("class")).toContain("border");
    expect(panel.getAttribute("class")).toContain("bg-");
  });

  it.each([1, 2, 3])("should render correctly for each level", (level) => {
    render(Panel, {
      level: level,
      children: childComponent,
    });
  });
});
