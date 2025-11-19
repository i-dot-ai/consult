import { render, fireEvent } from "@testing-library/svelte";
import { describe, it, expect, vi } from "vitest";
import Checkbox from "./Checkbox.svelte";

describe("Checkbox Component", () => {
  it("renders with basic props", () => {
    const { getByRole, getByLabelText } = render(Checkbox, {
      props: {
        id: "terms",
        label: "I agree to the terms and conditions"
      }
    });

    expect(getByLabelText("I agree to the terms and conditions")).toBeInTheDocument();
    expect(getByRole("checkbox")).toBeInTheDocument();
  });

  it("renders label with object configuration", () => {
    const { getByLabelText, container } = render(Checkbox, {
      props: {
        id: "terms",
        name: "terms",
        label: {
          text: "I agree to the terms",
          classes: "govuk-label--s"
        }
      }
    });

    expect(getByLabelText("I agree to the terms")).toBeInTheDocument();
    expect(container.querySelector('label')).toHaveClass('font-semibold');
  });

  it("renders label with string configuration", () => {
    const { getByLabelText } = render(Checkbox, {
      props: {
        id: "newsletter",
        label: "Subscribe to newsletter"
      }
    });

    expect(getByLabelText("Subscribe to newsletter")).toBeInTheDocument();
  });

  it("sets correct checked state", () => {
    const { getByRole } = render(Checkbox, {
      props: {
        id: "newsletter",
        label: "Subscribe",
        checked: true
      }
    });

    const checkbox = getByRole("checkbox");
    expect(checkbox).toBeChecked();
  });

  it("calls onchange when checked state changes", async () => {
    const onchange = vi.fn();
    const { getByRole } = render(Checkbox, {
      props: {
        id: "newsletter",
        label: "Subscribe",
        value: "newsletter-opt-in",
        onchange
      }
    });

    const checkbox = getByRole("checkbox");
    await fireEvent.click(checkbox);

    expect(onchange).toHaveBeenCalledWith(true, "newsletter-opt-in");
  });

  it("calls onchange without value when value not provided", async () => {
    const onchange = vi.fn();
    const { getByRole } = render(Checkbox, {
      props: {
        id: "newsletter",
        label: "Subscribe",
        onchange
      }
    });

    const checkbox = getByRole("checkbox");
    await fireEvent.click(checkbox);

    expect(onchange).toHaveBeenCalledWith(true, undefined);
  });

  it("renders hint text when provided", () => {
    const { getByText } = render(Checkbox, {
      props: {
        id: "newsletter",
        label: "Subscribe",
        hint: "You can unsubscribe at any time"
      }
    });

    expect(getByText("You can unsubscribe at any time")).toBeInTheDocument();
  });

  it("renders error message when provided", () => {
    const { getByText } = render(Checkbox, {
      props: {
        id: "terms",
        label: "Accept terms",
        errorMessage: "You must accept the terms"
      }
    });

    expect(getByText("You must accept the terms")).toBeInTheDocument();
  });

  it("applies error styling when error message present", () => {
    const { container } = render(Checkbox, {
      props: {
        id: "terms",
        label: "Accept terms",
        errorMessage: "Error message"
      }
    });

    const formGroup = container.firstChild;
    const checkbox = container.querySelector('input[type="checkbox"]');
    
    expect(formGroup).toHaveClass('border-l-4', 'border-red-600');
    expect(checkbox).toHaveClass('border-red-600');
  });

  it("hides label when hideLabel is true", () => {
    const { queryByText } = render(Checkbox, {
      props: {
        id: "hidden-checkbox",
        label: "Hidden Label",
        hideLabel: true
      }
    });

    expect(queryByText("Hidden Label")).not.toBeInTheDocument();
  });

  it("disables checkbox when disabled prop is true", () => {
    const { getByRole } = render(Checkbox, {
      props: {
        id: "disabled-checkbox",
        label: "Disabled",
        disabled: true
      }
    });

    const checkbox = getByRole("checkbox");
    expect(checkbox).toBeDisabled();
  });

  it("sets correct aria-describedby attributes", () => {
    const { getByRole } = render(Checkbox, {
      props: {
        id: "newsletter",
        label: "Subscribe",
        hint: "Hint text",
        errorMessage: "Error text"
      }
    });

    const checkbox = getByRole("checkbox");
    expect(checkbox).toHaveAttribute("aria-describedby", "newsletter-hint newsletter-error");
  });

  it("uses name prop or defaults to id", () => {
    const { getByRole } = render(Checkbox, {
      props: {
        id: "newsletter",
        name: "custom-name",
        label: "Subscribe"
      }
    });

    const checkbox = getByRole("checkbox");
    expect(checkbox).toHaveAttribute("name", "custom-name");
  });

  it("defaults name to id when name not provided", () => {
    const { getByRole } = render(Checkbox, {
      props: {
        id: "newsletter",
        label: "Subscribe"
      }
    });

    const checkbox = getByRole("checkbox");
    expect(checkbox).toHaveAttribute("name", "newsletter");
  });

  it("applies all GOV.UK label size classes", () => {
    const labelSizes = ['s', 'm', 'l', 'xl'];
    
    labelSizes.forEach(size => {
      const { container } = render(Checkbox, {
        props: {
          id: "test-checkbox",
          label: {
            text: "Test label",
            classes: `govuk-label--${size}`
          }
        }
      });

      const label = container.querySelector('label');
      const expectedClasses = {
        's': 'font-semibold',
        'm': 'font-semibold',
        'l': 'font-semibold',
        'xl': 'font-semibold'
      };
      expect(label).toHaveClass(expectedClasses[size]);
    });
  });

  it("sets checkbox value attribute when provided", () => {
    const { getByRole } = render(Checkbox, {
      props: {
        id: "newsletter",
        label: "Subscribe",
        value: "newsletter-subscription"
      }
    });

    const checkbox = getByRole("checkbox");
    expect(checkbox).toHaveValue("newsletter-subscription");
  });
});