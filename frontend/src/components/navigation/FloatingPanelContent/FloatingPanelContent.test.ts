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
    "Interactive tutorial for Finalising Themes",
    "View help documentation",
    "View our privacy policy",
  ])("renders subtitles", (itemText) => {
    render(FloatingPanelContent);

    expect(screen.getByText(itemText)).toBeInTheDocument();
  });

  // TODO: Refactor to mock setItem
  it.todo("clears onboardingKeys in localStorage", async () => {
    localStorage.setItem(OnboardingKeys.finaliseThemes, "true");
    localStorage.setItem(OnboardingKeys.finaliseThemesArchive, "true");

    expect(localStorage.getItem(OnboardingKeys.finaliseThemes)).toBeTruthy();
    expect(
      localStorage.getItem(OnboardingKeys.finaliseThemesArchive),
    ).toBeTruthy();

    render(FloatingPanelContent);

    const walkthroughButton = screen.getAllByRole("link").at(0);
    expect(walkthroughButton).toBeTruthy();

    const user = userEvent.setup();
    await user.click(walkthroughButton!);

    expect(localStorage.getItem(OnboardingKeys.finaliseThemes)).toBeFalsy();
    expect(
      localStorage.getItem(OnboardingKeys.finaliseThemesArchive),
    ).toBeFalsy();
  });

  it("matches snapshot", () => {
    const { container } = render(FloatingPanelContent);

    expect(container).toMatchSnapshot();
  });
});
