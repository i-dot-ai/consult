import { describe, expect, it } from "vitest";
import { render } from "@testing-library/svelte";

import MetricsSummary, { type Props } from "./MetricsSummary.svelte";

describe("MetricsSummary", () => {
  it("should render data", () => {
    const TEST_DATA: Props = {
      questionCount: 10,
      responseCount: 20,
      demoCount: 30,
    };

    const { container, getByText } = render(MetricsSummary, {
      questionCount: TEST_DATA.questionCount,
      responseCount: TEST_DATA.responseCount,
      demoCount: TEST_DATA.demoCount,
    });

    expect(getByText("Responses")).toBeInTheDocument();
    expect(getByText(TEST_DATA.responseCount)).toBeInTheDocument();

    expect(getByText("Questions")).toBeInTheDocument();
    expect(getByText(TEST_DATA.questionCount)).toBeInTheDocument();

    expect(getByText("Demographics")).toBeInTheDocument();
    expect(getByText(TEST_DATA.demoCount)).toBeInTheDocument();

    expect(container).toMatchSnapshot();
  });
});
