import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/svelte";
import userEvent from "@testing-library/user-event";

import WithExternalClick from "./WithExternalClick.svelte";
import { createRawSnippet } from "svelte";

describe("WithExternalClick", () => {
  const testData = {
    children: createRawSnippet(() => ({
      render: () => `
        <p data-testid="child-el">
          child content
        </p>
      `,
    }))
  }

  it("should call callback when an external element is clicked on", async () => {
    const onExternalClickMock = vi.fn();
    const user = userEvent.setup();

    render(WithExternalClick, {
      onExternalClick: onExternalClickMock,
      children: testData.children,
    });

    // Create an external element in the DOM
    const externalEl = document.createElement("div");
    externalEl.innerText = "External El";
    document.body.appendChild(document.createElement("div"));

    // If clicked an external element, callback should get called
    user.click(externalEl);
    waitFor(() => expect(onExternalClickMock).toHaveBeenCalledOnce())
  });

  it("should not call callback when an internal element is clicked on", async () => {
    const onExternalClickMock = vi.fn();
    const user = userEvent.setup();

    render(WithExternalClick, {
      onExternalClick: onExternalClickMock,
      children: testData.children,
    });

    // If clicked an inside element, callback shouldn't get called
    const childEl = screen.getByTestId("child-el");
    user.click(childEl);
    expect(onExternalClickMock).not.toHaveBeenCalled();
  });
});
