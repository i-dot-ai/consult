import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";

import ResponseAnalysis from "./ResponseAnalysis.svelte";

describe("ResponseAnalysis", () => {
  it("should render data", () => {
    render(ResponseAnalysis, {});

    expect(screen.getByText("Response refinement")).toBeInTheDocument();
    expect(
      screen.getByText(
        "In-depth analysis of individual consultation responses.",
      ),
    ).toBeInTheDocument();
  });
});
