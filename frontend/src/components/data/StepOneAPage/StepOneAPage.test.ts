import { describe, expect, it } from "vitest";
import { render, screen, waitFor } from "@testing-library/svelte";
import userEvent from "@testing-library/user-event";

import StepOneAPage from "./StepOneAPage.svelte";

describe("StepOneAPage", () => {
  it("should render order number text", () => {
    render(StepOneAPage);

    expect(
      screen.getByText("Step 1a: Export your data from your collection tool"),
    ).toBeInTheDocument();
  });

  it("should render hint accordion", () => {
    render(StepOneAPage);

    expect(
      screen.getByRole("button", { name: "hint-accordion" }),
    ).toBeInTheDocument();
  });

  it("should remove hint accordion if close button is clicked", async () => {
    render(StepOneAPage);

    const hintButton = screen.getByRole("button", { name: "hint-accordion" });

    expect(hintButton).toBeInTheDocument();

    const user = userEvent.setup();
    const hintCloseButton = screen.getByRole("button", {
      name: "close hint-accordion",
    });
    await user.click(hintCloseButton);

    await waitFor(() => {
      expect(hintButton).not.toBeInTheDocument();
    });
  });

  it("should reveal hint content if hint accordion is clicked", async () => {
    render(StepOneAPage);

    const hintAccordionContentTitle = "Why this matters:";

    expect(
      screen.queryByText(hintAccordionContentTitle),
    ).not.toBeInTheDocument();

    const hintButton = screen.getByRole("button", { name: "hint-accordion" });
    expect(hintButton).toBeInTheDocument();

    const user = userEvent.setup();
    await user.click(hintButton);

    await waitFor(() => {
      expect(screen.getByText(hintAccordionContentTitle)).toBeInTheDocument();
    });
  });

  it.each([
    { label: "Qualtrics tab", title: "Qualtrics export instructions" },
    { label: "Smart Survey tab", title: "Smart Survey export instructions" },
    { label: "Citizen Space tab", title: "Citizen Space export instructions" },
  ])(
    "should render smart survey content when its tab is clicked",
    async ({ label, title }) => {
      render(StepOneAPage);

      const tabButton = screen.getByRole("button", { name: label });

      const user = userEvent.setup();
      await user.click(tabButton);

      await waitFor(() => {
        expect(screen.getByText(title)).toBeInTheDocument();
      });
    },
  );

  it("should match snapshot", () => {
    const { container } = render(StepOneAPage);
    expect(container).toMatchSnapshot();
  });
});
