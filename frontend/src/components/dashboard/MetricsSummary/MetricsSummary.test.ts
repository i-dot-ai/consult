import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";

import MetricsSummary, { type Props } from "./MetricsSummary.svelte";

describe("MetricsSummary", () => {
  it("should render data", () => {
    const TEST_DATA: Props = {
      questionCount: 10,
      responseCount: 20,
      demoCount: 30,
    };

    const { container } = render(MetricsSummary, {
      questionCount: TEST_DATA.questionCount,
      responseCount: TEST_DATA.responseCount,
      demoCount: TEST_DATA.demoCount,
    });

    expect(screen.getByText("Responses")).toBeInTheDocument();
    expect(screen.getByText(TEST_DATA.responseCount)).toBeInTheDocument();

    expect(screen.getByText("Questions")).toBeInTheDocument();
    expect(screen.getByText(TEST_DATA.questionCount)).toBeInTheDocument();

    expect(screen.getByText("Demographics")).toBeInTheDocument();
    expect(screen.getByText(TEST_DATA.demoCount)).toBeInTheDocument();

    expect(container).toMatchSnapshot();
  });
});
