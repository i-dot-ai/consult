import { render, fireEvent, screen } from "@testing-library/svelte";
import { describe, it, expect, vi } from "vitest";

import Radio from "./Radio.svelte";

describe("Radio Component", () => {
  const items = [
    {
      value: "sign_off",
      text: "Populate Sign Off",
    },
    {
      value: "dashboard",
      text: "Populate Dashboard",
      checked: true,
    },
  ];

  it("renders all radio items", () => {
    render(Radio, { name: "action", items });

    expect(screen.getByLabelText("Populate Sign Off")).toBeInTheDocument();
    expect(screen.getByLabelText("Populate Dashboard")).toBeInTheDocument();
  });

  it("renders with legend when provided", () => {
    render(Radio, { name: "action", items, legend: "Choose an action" });

    expect(screen.getByText("Choose an action")).toBeInTheDocument();
  });

  it("sets checked state correctly", () => {
    render(Radio, { name: "action", items });

    const dashboardRadio = screen.getByLabelText("Populate Dashboard");
    const signOffRadio = screen.getByLabelText("Populate Sign Off");

    expect(dashboardRadio).toBeChecked();
    expect(signOffRadio).not.toBeChecked();
  });

  it("calls onchange when radio selection changes", async () => {
    const onchange = vi.fn();
    render(Radio, { name: "action", items, onchange });

    const signOffRadio = screen.getByLabelText("Populate Sign Off");
    await fireEvent.click(signOffRadio);

    expect(onchange).toHaveBeenCalledWith("sign_off");
    expect(signOffRadio).toBeChecked();
  });

  it("handles disabled items correctly", () => {
    render(Radio, {
      name: "action",
      items: [
        ...items,
        {
          value: "disabled",
          text: "Disabled Option",
          disabled: true,
        },
      ],
    });

    const disabledRadio = screen.getByLabelText("Disabled Option");
    expect(disabledRadio).toBeDisabled();
  });
});
