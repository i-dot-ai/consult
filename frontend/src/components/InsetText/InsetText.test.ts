import { render, screen } from "@testing-library/svelte";
import { describe, it, expect } from "vitest";

import InsetText from "./InsetText.svelte";

describe("InsetText Component", () => {
  it("renders with default variant", () => {
    render(InsetText, {}, { $$slots: { default: "Default content" } });

    const insetText = screen.getByText("Default content");
    expect(insetText.parentElement).toHaveClass(
      "border-blue-500",
      "bg-blue-50",
    );
  });

  it("renders with info variant", () => {
    render(
      InsetText,
      { variant: "info" },
      { $$slots: { default: "Info content" } },
    );

    const insetText = screen.getByText("Info content");
    expect(insetText.parentElement).toHaveClass(
      "border-blue-500",
      "bg-blue-50",
    );
  });

  it("renders with warning variant", () => {
    render(
      InsetText,
      { variant: "warning" },
      { $$slots: { default: "Warning content" } },
    );

    const insetText = screen.getByText("Warning content");
    expect(insetText.parentElement).toHaveClass(
      "border-yellow-500",
      "bg-yellow-50",
    );
  });

  it("renders with success variant", () => {
    render(
      InsetText,
      { variant: "success" },
      { $$slots: { default: "Success content" } },
    );

    const insetText = screen.getByText("Success content");
    expect(insetText.parentElement).toHaveClass(
      "border-green-500",
      "bg-green-50",
    );
  });

  it("renders with error variant", () => {
    render(
      InsetText,
      { variant: "error" },
      { $$slots: { default: "Error content" } },
    );

    const insetText = screen.getByText("Error content");
    expect(insetText.parentElement).toHaveClass("border-red-500", "bg-red-50");
  });

  it("applies custom className", () => {
    render(
      InsetText,
      { className: "my-custom-class" },
      { $$slots: { default: "Custom content" } },
    );

    const insetText = screen.getByText("Custom content");
    expect(insetText.parentElement).toHaveClass("my-custom-class");
  });

  it("applies default classes", () => {
    render(InsetText, {}, { $$slots: { default: "Test content" } });

    const insetText = screen.getByText("Test content");
    expect(insetText.parentElement).toHaveClass(
      "govuk-inset-text",
      "p-4",
      "border-l-4",
    );
  });

  it("renders slotted content", () => {
    render(InsetText, {}, { $$slots: { default: "Slotted content here" } });

    expect(screen.getByText("Slotted content here")).toBeInTheDocument();
  });
});
