import { render, screen } from "@testing-library/svelte";
import { describe, it, expect } from "vitest";
import { createRawSnippet } from "svelte";

import Details from "./Details.svelte";

describe("Details Component", () => {
  const props = {
    summaryText: "Test Summary",
    children: createRawSnippet(() => {
      return {
        render: () => `<div>Test content</div>`,
      };
    }),
  };

  it("renders with summary text", () => {
    render(Details, props);

    expect(screen.getByText("Test Summary")).toBeInTheDocument();
  });

  it("renders closed by default", () => {
    render(Details, props);

    expect(screen.getByRole("group")).not.toHaveAttribute("open");
  });

  it("renders open when open prop is true", () => {
    render(Details, { ...props, open: true });

    expect(screen.getByRole("group")).toHaveAttribute("open");
  });

  it("renders content in details text area", () => {
    render(Details, props);

    expect(screen.getByText("Test content")).toBeInTheDocument();
  });
});
