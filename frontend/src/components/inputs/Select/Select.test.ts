import { render, fireEvent, screen } from "@testing-library/svelte";
import { describe, it, expect, vi } from "vitest";

import Select from "./Select.svelte";

const mockItems = [
  { value: "consultation1", label: "Consultation Folder 1" },
  { value: "consultation2", label: "Consultation Folder 2" },
  { value: "consultation3", label: "Consultation Folder 3" },
];

describe("Select Component", () => {
  it("renders with basic props", () => {
    render(Select, {
      props: {
        id: "consultation_code",
        label: "Select consultation folder",
        items: mockItems,
      },
    });

    expect(
      screen.getByLabelText("Select consultation folder"),
    ).toBeInTheDocument();
    expect(screen.getByRole("combobox")).toBeInTheDocument();
  });

  it("renders all items", () => {
    render(Select, {
      props: {
        id: "consultation_code",
        items: mockItems,
      },
    });

    const options = screen.getAllByRole("option");
    expect(options).toHaveLength(3);
    expect(options[0]).toHaveTextContent("Consultation Folder 1");
    expect(options[1]).toHaveTextContent("Consultation Folder 2");
    expect(options[2]).toHaveTextContent("Consultation Folder 3");
  });

  it("renders label with object configuration", () => {
    render(Select, {
      props: {
        id: "consultation_code",
        name: "consultation_code",
        label: {
          text: "Select consultation folder",
          classes: "govuk-label--s",
        },
        items: mockItems,
      },
    });

    const label = screen.getByText("Select consultation folder");
    expect(label).toBeInTheDocument();
  });

  it("renders label with string configuration", () => {
    render(Select, {
      props: {
        id: "consultation_code",
        label: "Simple label text",
        items: mockItems,
      },
    });

    expect(screen.getByLabelText("Simple label text")).toBeInTheDocument();
  });

  it("sets correct selected value", () => {
    render(Select, {
      props: {
        id: "consultation_code",
        items: mockItems,
        value: "consultation2",
      },
    });

    const select = screen.getByRole("combobox");
    expect(select).toHaveValue("consultation2");
  });

  it("calls onchange when value changes", async () => {
    const onchange = vi.fn();
    render(Select, {
      props: {
        id: "consultation_code",
        items: mockItems,
        onchange,
      },
    });

    const select = screen.getByRole("combobox");
    await fireEvent.change(select, { target: { value: "consultation3" } });

    expect(onchange).toHaveBeenCalledWith("consultation3");
  });

  it("renders hint text when provided", () => {
    render(Select, {
      props: {
        id: "consultation_code",
        items: mockItems,
        hint: "Choose the consultation folder to import",
      },
    });

    expect(
      screen.getByText("Choose the consultation folder to import"),
    ).toBeInTheDocument();
  });

  it("shows error message and applies error styling", () => {
    const errorMessage = "Please select a consultation folder";
    render(Select, {
      props: {
        id: "consultation_code",
        label: "Select option",
        items: mockItems,
        hint: "Hint text",
        errorMessage,
      },
    });

    expect(screen.getByText(errorMessage)).toBeInTheDocument();

    const select = screen.getByRole("combobox");
    expect(select).toHaveAttribute(
      "aria-describedby",
      "consultation_code-hint consultation_code-error",
    );
  });

  it("hides label when hideLabel is true", () => {
    render(Select, {
      props: {
        id: "consultation_code",
        label: "Hidden Label",
        hideLabel: true,
        items: mockItems,
      },
    });

    expect(screen.queryByText("Hidden Label")).not.toBeInTheDocument();
  });

  it("disables select when disabled prop is true", () => {
    render(Select, {
      props: {
        id: "consultation_code",
        items: mockItems,
        disabled: true,
      },
    });

    const select = screen.getByRole("combobox");
    expect(select).toBeDisabled();
  });

  it("uses name prop or defaults to id", () => {
    render(Select, {
      props: {
        id: "consultation_code",
        name: "custom-name",
        items: mockItems,
      },
    });

    const select = screen.getByRole("combobox");
    expect(select).toHaveAttribute("name", "custom-name");
  });

  it("defaults name to id when name not provided", () => {
    render(Select, {
      props: {
        id: "consultation_code",
        items: mockItems,
      },
    });

    const select = screen.getByRole("combobox");
    expect(select).toHaveAttribute("name", "consultation_code");
  });
});
