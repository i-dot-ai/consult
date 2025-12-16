import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/svelte";
import userEvent from "@testing-library/user-event";

import WithExternalClick from "./WithExternalClick.svelte";
import { createRawSnippet } from "svelte";

describe("WithExternalClick", () => {
  it("should call callback only when an external element is clicked on", async () => {
    const onExternalClickMock = vi.fn();
    const user = userEvent.setup();

    render(WithExternalClick, {
      onExternalClick: onExternalClickMock,
      children: createRawSnippet(() => ({
        render: () => `
          <p data-testid="child-el">
            child content
          </p>
        `,
      }))
    });

    // Create an external element in the DOM
    const externalEl = document.createElement("div");
    externalEl.innerText = "External El";
    document.body.appendChild(document.createElement("div"));

    // If clicked and inside element, callback shouldn't get called
    const childEl = screen.getByTestId("child-el");
    user.click(childEl);
    expect(onExternalClickMock).not.toHaveBeenCalled();

    // If clicked and external element, callback should get called
    user.click(externalEl);
    waitFor(() => expect(onExternalClickMock).toHaveBeenCalledOnce())
  });
});
