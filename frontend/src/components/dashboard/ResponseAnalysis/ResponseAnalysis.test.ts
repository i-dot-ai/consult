import { describe, expect, it } from "vitest";
import { render } from "@testing-library/svelte";

import ResponseAnalysis from "./ResponseAnalysis.svelte";

describe("ResponseAnalysis", () => {
  it("should render data", () => {
    const { getByText } = render(ResponseAnalysis, {});

    expect(getByText("Response refinement"));
    expect(
      getByText("In-depth analysis of individual consultation responses."),
    );
  });
});
