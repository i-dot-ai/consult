import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";

import MetricsSummary, { type Props } from "./MetricsSummary.svelte";

describe("MetricsSummary", () => {
  it("should render data", () => {
    const TEST_DATA: Props = {
      questionCount: 10,
      responseCount: 20,
      demoCount: 30,
      respondentCount: 20,
    };

    const { container } = render(MetricsSummary, {
      questionCount: TEST_DATA.questionCount,
      responseCount: TEST_DATA.responseCount,
      demoCount: TEST_DATA.demoCount,
      respondentCount: TEST_DATA.respondentCount,
    });

    expect(screen.getByText("Answers")).toBeInTheDocument();
    expect(screen.getAllByText(TEST_DATA.responseCount)).toHaveLength(2);

    expect(screen.getByText("Questions")).toBeInTheDocument();
    expect(screen.getByText(TEST_DATA.questionCount)).toBeInTheDocument();

    expect(screen.getByText("Demographics")).toBeInTheDocument();
    expect(screen.getByText(TEST_DATA.demoCount)).toBeInTheDocument();

    expect(screen.getByText("Respondents")).toBeInTheDocument();
    expect(screen.getAllByText(TEST_DATA.respondentCount)).toHaveLength(2);

    expect(container).toMatchSnapshot();
  });
});
