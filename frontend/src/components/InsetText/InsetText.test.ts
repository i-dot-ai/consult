import { render, screen } from "@testing-library/svelte";
import { describe, it, expect } from "vitest";
import { createRawSnippet } from "svelte";

import InsetText from "./InsetText.svelte";

describe("InsetText Component", () => {
  const props = {
    children: createRawSnippet(() => {
      return {
        render: () => "Test content",
      };
    }),
  };

  it("renders child content", () => {
    render(InsetText, props);

    expect(screen.getByText("Test content")).toBeInTheDocument();
  });

  it("renders with different variants", () => {
    render(InsetText, { ...props, variant: "warning" });

    expect(screen.getByText("Test content")).toBeInTheDocument();
  });

  it("renders with custom className", () => {
    render(InsetText, { ...props, className: "my-custom-class" });

    expect(screen.getByText("Test content")).toBeInTheDocument();
  });
});
