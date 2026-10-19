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

  it.each([0, -1, -10])(
    "should render step 1 if step no is lower than 1",
    async (stepNo) => {
      render(StepTitle, { ...TEST_DATA, stepNo: stepNo });
      await waitFor(() => {
        expect(
          screen.getByText(`Step 1 of ${TEST_DATA.maxStepNo}`),
        ).toBeInTheDocument();
      });
    },
  );

  it("should render isExternal if is external", async () => {
    render(StepTitle, { ...TEST_DATA, isExternal: true });
    await waitFor(() => {
      expect(screen.getByText("Happens outside Consult")).toBeInTheDocument();
    });
  });

  it("should not render isExternal if is not external", async () => {
    render(StepTitle, { ...TEST_DATA, isExternal: false });
    await waitFor(() => {
      expect(
        screen.queryByText("Happens outside Consult"),
      ).not.toBeInTheDocument();
    });
  });

  it("should match snapshot", () => {
    const { container } = render(StepTitle, TEST_DATA);
    expect(container).toMatchSnapshot();
  });
});
