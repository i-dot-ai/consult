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
    "Prepare data outside Consult",
    "Upload & validate",
    "Define question structure",
  ])("should render card titles", (title) => {
    render(IntroPage);

    expect(screen.getByText(title)).toBeInTheDocument();
  });

  it.each([
    "Export from your collection tool and structure your files",
    "Check your data meets the required format",
    "Configure how each question should be analysed",
  ])("should render card subtitles", (subtitle) => {
    render(IntroPage);

    expect(screen.getByText(subtitle)).toBeInTheDocument();
  });

  it("should match snapshot", () => {
    const { container } = render(IntroPage);
    expect(container).toMatchSnapshot();
  });
});
