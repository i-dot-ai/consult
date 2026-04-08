import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";

import StepsTitle from "./StepsTitle.svelte";
import { TEST_DATA } from "./testData";

describe("StepsTitle", () => {
  const testData = TEST_DATA;

  it("should render title", () => {
    render(StepsTitle, testData);

    expect(screen.getByText(testData.text, { exact: false })).toBeInTheDocument();
  })

  it("should render dots", () => {
    render(StepsTitle, testData);

    screen.debug()

    expect(
      screen.getAllByTestId("dot-active")
    ).toHaveLength(1);

    expect(
      screen.getAllByTestId("dot-inactive")
    ).toHaveLength(4);    
  });

  it.each([1, 2, 3, 4, 5])("should render correct steps text based on current step", (currentStep) => {
    render(StepsTitle, {...testData, currentStep: currentStep});

    expect(
      screen.getByText(`Step ${currentStep} of ${testData.totalSteps}`, { exact: false })
    ).toBeInTheDocument();
  });

  it.each([5, 10, 100, 1000])("should render correct steps text based on total steps", (totalSteps) => {
    render(StepsTitle, {...testData, totalSteps: totalSteps});

    expect(
      screen.getByText(`Step ${testData.currentStep} of ${totalSteps}`, { exact: false })
    ).toBeInTheDocument();
  });

  it("should match snapshot", () => {
    const { container } = render(StepsTitle, testData);
    expect(container).toMatchSnapshot();
  });
});
