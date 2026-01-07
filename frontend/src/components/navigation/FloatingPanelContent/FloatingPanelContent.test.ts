import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";

import FloatingPanelContent from "./FloatingPanelContent.svelte";
import userEvent from "@testing-library/user-event";
import { OnboardingKeys } from "../../../global/types";

describe("FloatingPanelContent", () => {
  it.each(["Walkthrough", "Guidance", "Privacy notice"])(
    "renders titles",
    (itemText) => {
      render(FloatingPanelContent);

      expect(screen.getByText(itemText)).toBeInTheDocument();
    },
  );

  it.each([
    "Interactive tutorial for Theme Sign Off",
    "View help documentation",
    "View our privacy policy",
  ])("renders subtitles", (itemText) => {
    render(FloatingPanelContent);

    expect(screen.getByText(itemText)).toBeInTheDocument();
  });

  it("clears onboardingKeys in localStorage", async () => {
    localStorage.setItem(OnboardingKeys.themeSignoff, "true");
    localStorage.setItem(OnboardingKeys.themeSignoffArchive, "true");

    expect(localStorage.getItem(OnboardingKeys.themeSignoff)).toBeTruthy();
    expect(
      localStorage.getItem(OnboardingKeys.themeSignoffArchive),
    ).toBeTruthy();

    render(FloatingPanelContent);

    const walkthroughButton = screen.getAllByRole("link").at(0);
    expect(walkthroughButton).toBeTruthy();

    const user = userEvent.setup();
    await user.click(walkthroughButton!);

    expect(localStorage.getItem(OnboardingKeys.themeSignoff)).toBeFalsy();
    expect(
      localStorage.getItem(OnboardingKeys.themeSignoffArchive),
    ).toBeFalsy();
  });

  it("matches snapshot", () => {
    const { container } = render(FloatingPanelContent);

    expect(container).toMatchSnapshot();
  });
});
