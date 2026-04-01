import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/svelte";

import IntroPage from "./IntroPage.svelte";

describe("IntroPage", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("should alternate active card every 2 seconds", async () => {
    render(IntroPage);

    const cards = screen.getAllByTestId("intro-card");

    expect(cards.at(0)).toHaveAttribute("aria-current");
    expect(cards.at(1)).not.toHaveAttribute("aria-current");
    expect(cards.at(2)).not.toHaveAttribute("aria-current");

    await vi.advanceTimersByTimeAsync(2000);

    expect(cards.at(0)).not.toHaveAttribute("aria-current");
    expect(cards.at(1)).toHaveAttribute("aria-current");
    expect(cards.at(2)).not.toHaveAttribute("aria-current");

    await vi.advanceTimersByTimeAsync(2000);

    expect(cards.at(0)).not.toHaveAttribute("aria-current");
    expect(cards.at(1)).not.toHaveAttribute("aria-current");
    expect(cards.at(2)).toHaveAttribute("aria-current");

    await vi.advanceTimersByTimeAsync(2000);

    expect(cards.at(0)).toHaveAttribute("aria-current");
    expect(cards.at(1)).not.toHaveAttribute("aria-current");
    expect(cards.at(2)).not.toHaveAttribute("aria-current");
  });

  it.each([
    "Prepare your data",
    "Upload & review",
    "Configure questions",
  ])("should render card titles", (title) => {
    render(IntroPage);

    expect(screen.getByText(title)).toBeInTheDocument();
  });

  it.each([
    "Export from your collection tool and get to know your data",
    "Upload your file and review validation results",
    "Confirm question types and configure closed questions",
  ])("should render card subtitles", (subtitle) => {
    render(IntroPage);

    expect(screen.getByText(subtitle)).toBeInTheDocument();
  });

  it("should match snapshot", () => {
    const { container } = render(IntroPage);
    expect(container).toMatchSnapshot();
  });
});
