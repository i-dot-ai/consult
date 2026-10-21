import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/svelte";

import RadioCards from "./RadioCards.svelte";

const items = [
  { value: "qualtrics", text: "Qualtrics", hint: "Survey platform" },
  {
    value: "citizen-space",
    text: "Citizen Space",
    hint: "Consultation platform",
  },
];

describe("RadioCards", () => {
  it("renders the legend, hint, and one radio per item", () => {
    render(RadioCards, {
      name: "tool",
      legend: "Which tool did you use?",
      hint: "Pick the one the responses were collected in.",
      items,
      value: "qualtrics",
      onchange: vi.fn(),
    });

    expect(
      screen.getByRole("group", { name: "Which tool did you use?" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Pick the one the responses were collected in."),
    ).toBeInTheDocument();
    expect(screen.getAllByRole("radio")).toHaveLength(2);
    expect(screen.getByText("Survey platform")).toBeInTheDocument();
  });

  it("checks the radio matching value", () => {
    render(RadioCards, {
      name: "tool",
      legend: "Which tool did you use?",
      items,
      value: "citizen-space",
      onchange: vi.fn(),
    });

    expect(screen.getByLabelText(/Citizen Space/)).toBeChecked();
    expect(screen.getByLabelText(/Qualtrics/)).not.toBeChecked();
  });

  it("calls onchange with the clicked value", async () => {
    const onchange = vi.fn();
    render(RadioCards, {
      name: "tool",
      legend: "Which tool did you use?",
      items,
      value: "qualtrics",
      onchange,
    });

    await fireEvent.click(screen.getByLabelText(/Citizen Space/));

    expect(onchange).toHaveBeenCalledWith("citizen-space");
  });
});
