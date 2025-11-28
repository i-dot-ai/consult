import { render, fireEvent } from "@testing-library/svelte";
import { describe, it, expect, vi } from "vitest";
import '@testing-library/jest-dom/vitest';

import Select from "./Select.svelte";

const mockItems = [
  { value: "consultation1", label: "Consultation Folder 1" },
  { value: "consultation2", label: "Consultation Folder 2" },
  { value: "consultation3", label: "Consultation Folder 3" }
];

describe("Select Component", () => {
  it("renders with basic props", () => {
    const { getByRole, getByLabelText } = render(Select, {
      props: {
        id: "consultation_code",
        label: "Select consultation folder",
        items: mockItems
      }
    });

    expect(getByLabelText("Select consultation folder")).toBeInTheDocument();
    expect(getByRole("combobox")).toBeInTheDocument();
  });

  it("renders all items", () => {
    const { getAllByRole } = render(Select, {
      props: {
        id: "consultation_code",
        items: mockItems
      }
    });

    const options = getAllByRole("option");
    expect(options).toHaveLength(3);
    expect(options[0]).toHaveTextContent("Consultation Folder 1");
    expect(options[1]).toHaveTextContent("Consultation Folder 2");
    expect(options[2]).toHaveTextContent("Consultation Folder 3");
  });

  it("renders label with object configuration", () => {
    const { getByLabelText, container } = render(Select, {
      props: {
        id: "consultation_code",
        name: "consultation_code",
        label: {
          text: "Select consultation folder",
          classes: "govuk-label--s"
        },
        items: mockItems
      }
    });

    const label = container.querySelector('.govuk-label');
    expect(getByLabelText("Select consultation folder")).toBeInTheDocument();
  });

  it("renders label with string configuration", () => {
    const { getByLabelText } = render(Select, {
      props: {
        id: "consultation_code",
        label: "Simple label text",
        items: mockItems
      }
    });

    expect(getByLabelText("Simple label text")).toBeInTheDocument();
  });

  it("sets correct selected value", () => {
    const { getByRole } = render(Select, {
      props: {
        id: "consultation_code",
        items: mockItems,
        value: "consultation2"
      }
    });

    const select = getByRole("combobox");
    expect(select).toHaveValue("consultation2");
  });

  it("calls onchange when value changes", async () => {
    const onchange = vi.fn();
    const { getByRole } = render(Select, {
      props: {
        id: "consultation_code",
        items: mockItems,
        onchange
      }
    });

    const select = getByRole("combobox");
    await fireEvent.change(select, { target: { value: "consultation3" } });

    expect(onchange).toHaveBeenCalledWith("consultation3");
  });

  it("renders hint text when provided", () => {
    const { getByText } = render(Select, {
      props: {
        id: "consultation_code",
        items: mockItems,
        hint: "Choose the consultation folder to import"
      }
    });

    expect(getByText("Choose the consultation folder to import")).toBeInTheDocument();
  });

  it("renders error message when provided", () => {
    const { getByText } = render(Select, {
      props: {
        id: "consultation_code",
        items: mockItems,
        errorMessage: "Please select a consultation folder"
      }
    });

    expect(getByText("Please select a consultation folder")).toBeInTheDocument();
  });

  it("hides label when hideLabel is true", () => {
    const { queryByText } = render(Select, {
      props: {
        id: "consultation_code",
        label: "Hidden Label",
        hideLabel: true,
        items: mockItems
      }
    });

    expect(queryByText("Hidden Label")).not.toBeInTheDocument();
  });

  it("disables select when disabled prop is true", () => {
    const { getByRole } = render(Select, {
      props: {
        id: "consultation_code",
        items: mockItems,
        disabled: true
      }
    });

    const select = getByRole("combobox");
    expect(select).toBeDisabled();
  });

  it("sets correct aria-describedby attributes", () => {
    const { getByRole } = render(Select, {
      props: {
        id: "consultation_code",
        items: mockItems,
        hint: "Hint text",
        errorMessage: "Error text"
      }
    });

    const select = getByRole("combobox");
    expect(select).toHaveAttribute("aria-describedby", "consultation_code-hint consultation_code-error");
  });

  it("uses name prop or defaults to id", () => {
    const { getByRole } = render(Select, {
      props: {
        id: "consultation_code",
        name: "custom-name", 
        items: mockItems
      }
    });

    const select = getByRole("combobox");
    expect(select).toHaveAttribute("name", "custom-name");
  });

  it("defaults name to id when name not provided", () => {
    const { getByRole } = render(Select, {
      props: {
        id: "consultation_code",
        items: mockItems
      }
    });

    const select = getByRole("combobox");
    expect(select).toHaveAttribute("name", "consultation_code");
  });
});