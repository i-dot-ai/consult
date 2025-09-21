import { afterEach, describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { render, cleanup, screen } from "@testing-library/svelte";

import PopoverTest from "./PopoverTest.svelte";

describe("Popover", () => {
  afterEach(() => cleanup());

  it("should toggle panel when trigger is clicked", async () => {
    vi.mock("svelte/transition");

    const PANEL_CONTENT = "Panel Content";
    const user = userEvent.setup();

    const { getByText, queryByText } = render(PopoverTest, {
      panelContent: PANEL_CONTENT,
    });

    expect(queryByText(PANEL_CONTENT)).toBeNull();

    const button = screen.getByRole("button");
    await user.click(button);

    expect(getByText(PANEL_CONTENT));
  });

  it("should be open or close initially based on the open prop", async () => {
    vi.mock("svelte/transition");

    const PANEL_CONTENT = "Panel Content";
    const user = userEvent.setup();

    const { getByText, queryByText } = render(PopoverTest, {
      panelContent: PANEL_CONTENT,
      open: true,
    });

    expect(getByText(PANEL_CONTENT));

    const button = screen.getByRole("button");
    await user.click(button);

    expect(queryByText(PANEL_CONTENT)).toBeNull();
  });

  it("should render trigger content and label", async () => {
    vi.mock("svelte/transition");

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
