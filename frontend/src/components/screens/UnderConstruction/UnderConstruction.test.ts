import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";

import UnderConstruction from "./UnderConstruction.svelte";

describe("UnderConstruction", () => {
  it("should render warning text", async () => {
    render(UnderConstruction);

    expect(
      screen.getByRole("heading", { name: "Under Construction" }),
    ).toBeInTheDocument();
  });

  it("should match snapshot", () => {
    const { container } = render(UnderConstruction);
    expect(container).toMatchSnapshot();
  });
});
