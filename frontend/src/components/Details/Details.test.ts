import { render } from "@testing-library/svelte";
import { describe, it, expect } from "vitest";
import '@testing-library/jest-dom/vitest';

import { createRawSnippet } from "svelte";

import Details from "./Details.svelte";

describe("Details Component", () => {
  it("renders with summary text", () => {
    const { getByText } = render(Details, {
      props: {
        summaryText: "Test Summary",
        children: createRawSnippet(() => {
          return {
            render: () => `<div>Test content</div>`,
          };
        }),
      }
    });

    expect(getByText("Test Summary")).toBeInTheDocument();
  });

  it("renders closed by default", () => {
    const { container } = render(Details, {
      props: {
        summaryText: "Test Summary", 
        children: createRawSnippet((name) => {
          return {
            render: () => `<div>Test content</div>`,
          };
        }),
      }
    });

    const details = container.querySelector("details");
    expect(details).not.toHaveAttribute("open");
  });

  it("renders open when open prop is true", () => {
    const { container } = render(Details, {
      props: {
        summaryText: "Test Summary",
        children: createRawSnippet((name) => {
          return {
            render: () => `<div>Test content</div>`,
          };
        }),
        open: true
      }
    });

    const details = container.querySelector("details");
    expect(details).toHaveAttribute("open");
  });

  it("renders content in details text area", () => {
    const { getByText } = render(Details, {
      props: {
        summaryText: "Test Summary",
        children: createRawSnippet((name) => {
          return {
            render: () => `<div>Test content</div>`,
          };
        })
      }
    });

    expect(getByText("Test content")).toBeInTheDocument();
  });
});