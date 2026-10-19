import { describe, expect, it } from "vitest";
import { render, screen, waitFor } from "@testing-library/svelte";

import StepTitle from "./StepTitle.svelte";
import { TEST_DATA } from "./testData";

describe("StepTitle", () => {
  it("should render title", async () => {
    render(StepTitle, TEST_DATA);
    await waitFor(() => {
      expect(screen.getByText(TEST_DATA.title)).toBeInTheDocument();
    });
  });

  it("should render max step no if step no is higher", async () => {
    render(StepTitle, { ...TEST_DATA, maxStepNo: 1, stepNo: 6 });
    await waitFor(() => {
      expect(screen.getByText("Step 1 of 1")).toBeInTheDocument();
    });
  });

  it("should match snapshot", () => {
    const { container } = render(StepTitle, TEST_DATA);
    expect(container).toMatchSnapshot();
  });
});
