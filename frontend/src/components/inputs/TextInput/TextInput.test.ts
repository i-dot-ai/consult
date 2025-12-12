import { describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { render, screen, fireEvent } from "@testing-library/svelte";

import TextInput from "./TextInput.svelte";

describe("TextInput", () => {
  it("should call setValue func", async () => {
    const handleInputMock = vi.fn();

    render(TextInput, {
      id: "test-input",
      value: "",
      label: "Test Input",
      setValue: handleInputMock,
    });

    const input = screen.getByLabelText("Test Input");

    await fireEvent.input(input, { target: { value: "new value" } });
    expect(handleInputMock).toHaveBeenCalledExactlyOnceWith("new value");
  });

  it("should render props", async () => {
    render(TextInput, {
      id: "test-input",
      value: "",
      label: "Test Input",
      placeholder: "Test Placeholder",
    });

    expect(screen.getByRole("textbox")).toBeInTheDocument();
    expect(screen.getByLabelText("Test Input")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Test Placeholder")).toBeInTheDocument();
  });

  it("should hide label if hideLabel is true", async () => {
    render(TextInput, {
      id: "test-input",
      value: "",
      label: "Test Input",
      hideLabel: true,
    });

    expect(screen.queryByText("Test Input")).toHaveClass("sr-only");
  });

  it("should have a reset button if variant is search", async () => {
    const setValueMock = vi.fn();
    const user = userEvent.setup();

    render(TextInput, {
      id: "test-input",
      value: "test value",
      label: "Test Input",
      variant: "search",
      setValue: setValueMock,
    });

    const resetButton = screen.getByRole("button");
    await user.click(resetButton);

    expect(setValueMock).toHaveBeenCalledWith("");
  });
});
