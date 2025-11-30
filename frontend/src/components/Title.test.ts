import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";

import Title from "./Title.svelte";

describe("Title", () => {
  it("renders correct text", () => {
    render(Title, { text: "Test text" });

    expect(screen.getByText("Test text")).toBeInTheDocument();
  });

  it.each([1, 2, 3, 4, 5, 6])("renders correct tag", (level) => {
    render(Title, { level, text: "Test text" });

    expect(screen.getByRole("heading", { level })).toBeInTheDocument();
  });
});
