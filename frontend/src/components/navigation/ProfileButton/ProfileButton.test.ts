import { describe, expect, it } from "vitest";
import userEvent from "@testing-library/user-event";
import { render, screen, waitFor } from "@testing-library/svelte";

import ProfileButton from "./ProfileButton.svelte";

describe("Header", () => {
  it("should render contents", async () => {
    const user = userEvent.setup();

    render(ProfileButton);

    // Links initially hidden
    expect(screen.queryByText("Profile")).toBeFalsy();
    expect(screen.queryByText("Sign Out")).toBeFalsy();

    // Click on button to expand links
    const button = screen.getByRole("button");
    user.click(button);

    // Links should be revealed after the click
    waitFor(() => {
      expect(screen.getByText("Profile")).toBeInTheDocument();
      expect(screen.getByText("Sign Out")).toBeInTheDocument();
    })
  });
});
