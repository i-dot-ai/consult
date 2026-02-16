import { describe, expect, it } from "vitest";
import userEvent from "@testing-library/user-event";
import { render, screen, waitFor } from "@testing-library/svelte";

import ProfileButton from "./ProfileButton.svelte";

describe("ProfileButton", () => {
  it("should render Sign Out when signed in", async () => {
    const user = userEvent.setup();

    render(ProfileButton, { isSignedIn: true });

    // Links initially hidden
    expect(screen.queryByText("Sign Out")).toBeFalsy();

    // Click on button to expand links
    const button = screen.getByRole("button");
    await user.click(button);

    // Sign Out should be revealed after the click
    await waitFor(() => {
      expect(screen.getByText("Sign Out")).toBeInTheDocument();
    });
  });

  it("should not render Sign Out when not signed in", async () => {
    const user = userEvent.setup();

    render(ProfileButton, { isSignedIn: false });

    // Click on button to expand panel
    const button = screen.getByRole("button");
    await user.click(button);

    // Sign Out should not be present when not signed in
    await waitFor(() => {
      expect(screen.queryByText("Sign Out")).not.toBeInTheDocument();
    });
  });

  it("matches snapshot", () => {
    const { container } = render(ProfileButton);
    expect(container).toMatchSnapshot();
  });
});
