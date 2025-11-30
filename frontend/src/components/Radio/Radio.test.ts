import { render, fireEvent, screen } from "@testing-library/svelte";
import { describe, it, expect, vi } from "vitest";
import Radio from "./Radio.svelte";

const mockItems = [
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

describe("Radio Component", () => {
  it("renders all radio items", () => {
    render(Radio, {
      props: {
        name: "action",
        items: mockItems,
      },
    });

    expect(screen.getByText("Populate Sign Off")).toBeInTheDocument();
    expect(screen.getByText("Populate Dashboard")).toBeInTheDocument();
  });

  it("renders with legend when provided", () => {
    render(Radio, {
      props: {
        name: "action",
        items: mockItems,
        legend: "Choose an action",
      },
    });

    expect(screen.getByText("Choose an action")).toBeInTheDocument();
  });

  it("sets checked state correctly", () => {
    const { container } = render(Radio, {
      props: {
        name: "action",
        items: mockItems,
      },
    });

    const dashboardRadio = container.querySelector('input[value="dashboard"]');
    const signOffRadio = container.querySelector('input[value="sign_off"]');

    expect(dashboardRadio).toBeChecked();
    expect(signOffRadio).not.toBeChecked();
  });

  it("calls onchange when radio selection changes", async () => {
    const onchange = vi.fn();
    const { container } = render(Radio, {
      props: {
        name: "action",
        items: mockItems,
        onchange,
      },
    });

    const signOffRadio = container.querySelector('input[value="sign_off"]');
    await fireEvent.click(signOffRadio);

    expect(onchange).toHaveBeenCalledWith("sign_off");
  });

  it("respects value prop override", () => {
    const { container } = render(Radio, {
      props: {
        name: "action",
        items: mockItems,
        value: "sign_off",
      },
    });

    const dashboardRadio = container.querySelector('input[value="dashboard"]');
    const signOffRadio = container.querySelector('input[value="sign_off"]');

    expect(signOffRadio).toBeChecked();
    expect(dashboardRadio).not.toBeChecked();
  });

  it("handles disabled items correctly", () => {
    const itemsWithDisabled = [
      ...mockItems,
      {
        value: "disabled",
        text: "Disabled Option",
        disabled: true,
      },
    ];

    const { container } = render(Radio, {
      props: {
        name: "action",
        items: itemsWithDisabled,
      },
    });

    const disabledRadio = container.querySelector('input[value="disabled"]');
    expect(disabledRadio).toBeDisabled();
  });

  it("generates correct id and name attributes", () => {
    const { container } = render(Radio, {
      props: {
        name: "test-action",
        items: mockItems,
      },
    });

    const signOffRadio = container.querySelector('input[value="sign_off"]');
    const signOffLabel = container.querySelector(
      'label[for="test-action-sign_off"]',
    );

    expect(signOffRadio).toHaveAttribute("id", "test-action-sign_off");
    expect(signOffRadio).toHaveAttribute("name", "test-action");
    expect(signOffLabel).toBeInTheDocument();
  });
});
