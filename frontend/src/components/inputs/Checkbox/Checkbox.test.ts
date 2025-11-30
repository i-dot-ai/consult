import { render, fireEvent, screen } from "@testing-library/svelte";
import { describe, it, expect, vi } from "vitest";
import Checkbox from "./Checkbox.svelte";

describe("Checkbox Component", () => {
  it("renders with basic props", () => {
    render(Checkbox, {
      props: {
        id: "terms",
        label: "I agree to the terms and conditions",
      },
    });

    expect(
      screen.getByLabelText("I agree to the terms and conditions"),
    ).toBeInTheDocument();
    expect(screen.getByRole("checkbox")).toBeInTheDocument();
  });

  it("renders label with object configuration", () => {
    render(Checkbox, {
      props: {
        id: "terms",
        name: "terms",
        label: {
          text: "I agree to the terms",
          classes: "govuk-label--s",
        },
      },
    });

    const label = screen.getByText("I agree to the terms");
    expect(label).toBeInTheDocument();
    expect(label).toHaveClass("font-semibold");
  });

  it("renders label with string configuration", () => {
    render(Checkbox, {
      props: {
        id: "newsletter",
        label: "Subscribe to newsletter",
      },
    });

    expect(
      screen.getByLabelText("Subscribe to newsletter"),
    ).toBeInTheDocument();
  });

  it("sets correct checked state", () => {
    render(Checkbox, {
      props: {
        id: "newsletter",
        label: "Subscribe",
        checked: true,
      },
    });

    const checkbox = screen.getByRole("checkbox");
    expect(checkbox).toBeChecked();
  });

  it("calls onchange when checked state changes", async () => {
    const onchange = vi.fn();
    render(Checkbox, {
      props: {
        id: "newsletter",
        label: "Subscribe",
        value: "newsletter-opt-in",
        onchange,
      },
    });

    const checkbox = screen.getByRole("checkbox");
    await fireEvent.click(checkbox);

    expect(onchange).toHaveBeenCalledWith(true, "newsletter-opt-in");
  });

  it("calls onchange without value when value not provided", async () => {
    const onchange = vi.fn();
    render(Checkbox, {
      props: {
        id: "newsletter",
        label: "Subscribe",
        onchange,
      },
    });

    const checkbox = screen.getByRole("checkbox");
    await fireEvent.click(checkbox);

    expect(onchange).toHaveBeenCalledWith(true, undefined);
  });

  it("renders hint text when provided", () => {
    render(Checkbox, {
      props: {
        id: "newsletter",
        label: "Subscribe",
        hint: "You can unsubscribe at any time",
      },
    });

    expect(
      screen.getByText("You can unsubscribe at any time"),
    ).toBeInTheDocument();
  });

  it("renders error message when provided", () => {
    render(Checkbox, {
      props: {
        id: "terms",
        label: "Accept terms",
        errorMessage: "You must accept the terms",
      },
    });

    expect(screen.getByText("You must accept the terms")).toBeInTheDocument();
  });

  it("applies error styling when error message present", () => {
    render(Checkbox, {
      props: {
        id: "terms",
        label: "Accept terms",
        errorMessage: "Error message",
      },
    });

    const checkbox = screen.getByRole("checkbox");
    expect(checkbox).toHaveClass("border-red-600");
  });

  it("hides label when hideLabel is true", () => {
    render(Checkbox, {
      props: {
        id: "hidden-checkbox",
        label: "Hidden Label",
        hideLabel: true,
      },
    });

    expect(screen.queryByText("Hidden Label")).not.toBeInTheDocument();
  });

  it("disables checkbox when disabled prop is true", () => {
    render(Checkbox, {
      props: {
        id: "disabled-checkbox",
        label: "Disabled",
        disabled: true,
      },
    });

    const checkbox = screen.getByRole("checkbox");
    expect(checkbox).toBeDisabled();
  });

  it("sets correct aria-describedby attributes", () => {
    render(Checkbox, {
      props: {
        id: "newsletter",
        label: "Subscribe",
        hint: "Hint text",
        errorMessage: "Error text",
      },
    });

    const checkbox = screen.getByRole("checkbox");
    expect(checkbox).toHaveAttribute(
      "aria-describedby",
      "newsletter-hint newsletter-error",
    );
  });

  it("uses name prop or defaults to id", () => {
    render(Checkbox, {
      props: {
        id: "newsletter",
        name: "custom-name",
        label: "Subscribe",
      },
    });

    const checkbox = screen.getByRole("checkbox");
    expect(checkbox).toHaveAttribute("name", "custom-name");
  });

  it("defaults name to id when name not provided", () => {
    render(Checkbox, {
      props: {
        id: "newsletter",
        label: "Subscribe",
      },
    });

    const checkbox = screen.getByRole("checkbox");
    expect(checkbox).toHaveAttribute("name", "newsletter");
  });

  it("applies all GOV.UK label size classes", () => {
    const labelSizes = ["s", "m", "l", "xl"] as const;
    const expectedClasses = {
      s: "font-semibold",
      m: "text-lg",
      l: "text-2xl",
      xl: "text-3xl",
    };

    labelSizes.forEach((size) => {
      render(Checkbox, {
        props: {
          id: "test-checkbox",
          label: {
            text: `Test label; ${size}`,
            classes: `govuk-label--${size}`,
          },
        },
      });

      const label = screen.getByText(`Test label; ${size}`);
      expect(label).toBeInTheDocument();
      expect(label).toHaveClass(expectedClasses[size]);
    });
  });
});
