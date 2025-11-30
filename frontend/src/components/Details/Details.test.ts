import { render, screen } from "@testing-library/svelte";
import { describe, it, expect } from "vitest";
import { createRawSnippet } from "svelte";

import Details from "./Details.svelte";

describe("Details Component", () => {
  const props = {
    summaryText: "Test Summary",
    children: createRawSnippet(() => ({
      render: () => `<p>Test content</p>`,
    })),
  };

  it("renders with summary text", () => {
    render(Details, { props });

    expect(screen.getByText("Test Summary")).toBeInTheDocument();
  });

  it("renders closed by default", () => {
    const { container } = render(Details, { props });

    const details = container.querySelector("details");
    expect(details).not.toHaveAttribute("open");
  });

  it("renders open when open prop is true", () => {
    const { container } = render(Details, { props: { ...props, open: true } });

    const details = container.querySelector("details");
    expect(details).toHaveAttribute("open");
  });

  it("renders content in details text area", () => {
    render(Details, { props });

    expect(screen.getByText("Test content")).toBeInTheDocument();
  });
});
