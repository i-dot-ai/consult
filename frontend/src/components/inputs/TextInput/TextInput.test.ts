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

    expect(handleInputMock).toHaveBeenCalledOnce();
    expect(handleInputMock).toHaveBeenCalledWith("new value");
  });

  it("should render props", async () => {
    const { container } = render(TextInput, {
      id: "test-input",
      value: "",
      label: "Test Input",
      placeholder: "Test Placeholder",
    });
    expect(container.querySelector("#test-input")).toBeTruthy();
    expect(
      container.querySelector(`input[placeholder="Test Placeholder"]`),
    ).toBeTruthy();
  });

  it("should hide label if hideLabel is true", async () => {
    const { container } = render(TextInput, {
      id: "test-input",
      value: "",
      label: "Test Input",
      hideLabel: true,
    });
    expect(container.querySelector("label.sr-only")).toBeTruthy();
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
