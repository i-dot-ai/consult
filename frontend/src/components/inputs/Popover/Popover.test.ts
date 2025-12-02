import { describe, expect, it } from "vitest";
import userEvent from "@testing-library/user-event";
import { render, screen } from "@testing-library/svelte";

import PopoverTest from "./PopoverTest.svelte";

describe("Popover", () => {
  it("should toggle panel when trigger is clicked", async () => {
    const PANEL_CONTENT = "Panel Content";
    const user = userEvent.setup();

    render(PopoverTest, {
      panelContent: PANEL_CONTENT,
    });

    expect(screen.queryByText(PANEL_CONTENT)).toBeNull();

    const button = screen.getByRole("button");
    await user.click(button);

    expect(screen.getByText(PANEL_CONTENT)).toBeInTheDocument();
  });

  it("should be open or close initially based on the open prop", async () => {
    const PANEL_CONTENT = "Panel Content";
    const user = userEvent.setup();

    render(PopoverTest, {
      panelContent: PANEL_CONTENT,
      open: true,
    });

    expect(screen.getByText(PANEL_CONTENT)).toBeInTheDocument();

    const button = screen.getByRole("button");
    await user.click(button);

    expect(screen.queryByText(PANEL_CONTENT)).toBeNull();
  });

  it("should render trigger content and label", async () => {
    const TRIGGER_CONTENT = "trigger content";
    const LABEL_CONTENT = "label content";

    render(PopoverTest, {
      panelContent: "content",
      triggerContent: TRIGGER_CONTENT,
      label: LABEL_CONTENT,
    });

    const button = screen.getByRole("button");
    expect(button.getAttribute("aria-label")).toEqual(LABEL_CONTENT);
    expect(button.innerHTML).toContain(TRIGGER_CONTENT);
  });
});
