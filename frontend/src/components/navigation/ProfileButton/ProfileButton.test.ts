import { describe, expect, it } from "vitest";
import userEvent from "@testing-library/user-event";
import { render, screen, waitFor } from "@testing-library/svelte";

import ProfileButton from "./ProfileButton.svelte";

describe("Header", () => {
  const AUTH_LINK_LABELS = [
    { value: true, text: "Sign Out" },
    { value: false, text: "Sign In" },
  ];

  it.each([true, false])(
    "should render correct contents",
    async (isSignedIn) => {
      const user = userEvent.setup();

      const labelText = AUTH_LINK_LABELS.find(
        (label) => label.value === isSignedIn,
      )!.text;

      render(ProfileButton, { isSignedIn });

      // Links initially hidden
      expect(screen.queryByText(labelText)).toBeFalsy();

      // Click on button to expand links
      const button = screen.getByRole("button");
      await user.click(button);

      // Links should be revealed after the click
      await waitFor(() => {
        expect(screen.getByText(labelText)).toBeInTheDocument();
      });
    },
  );
});
