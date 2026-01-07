import { describe, expect, it } from "vitest";
import userEvent from "@testing-library/user-event";
import { render, screen } from "@testing-library/svelte";

import FloatingPanel, { type Props } from "./FloatingPanel.svelte";
import { createRawSnippet } from "svelte";
import { derandomize } from "../../../global/utils";
import FloatingPanelStory from "./FloatingPanelStory.svelte";

describe("FloatingPanel", () => {
  const testData: Props = {
    children: createRawSnippet(() => ({
      render: () => `<p>Child Content</p>`,
    })),
  };

  it.each(["left", "right"])("renders correct direction", (direction) => {
    const { container } = render(FloatingPanel, {
      direction: direction as Props["direction"],
      children: testData.children,
    });

    derandomize(container, ["id", "aria-controls"]);

    expect(container).toMatchSnapshot();
  });

  it("displays panel when button is clicked", async () => {
    render(FloatingPanel, testData);

    const user = userEvent.setup();
    const button = screen.getAllByRole("button").at(0);
    expect(button).toBeTruthy();

    // Click to reveal contents
    await user.click(button!);
    expect(screen.getByText("Child Content")).toBeInTheDocument();

    // Click to hide contents
    await user.click(button!);
    expect(screen.queryByText("Child Content")).not.toBeInTheDocument();
  });

  it("should have a story configured correctly", () => {
    expect(FloatingPanelStory).toHaveProperty("name", "FloatingPanel");
    expect(FloatingPanelStory).toHaveProperty("component", FloatingPanel);
    expect(FloatingPanelStory).toHaveProperty("props");

    const propsDefined = FloatingPanelStory.props.map((prop) => prop.name);
    expect(propsDefined).toEqual(["direction", "children"]);
  });
});
