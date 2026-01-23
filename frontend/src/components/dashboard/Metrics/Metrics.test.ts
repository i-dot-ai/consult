import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";

import Metrics from "./Metrics.svelte";

describe("Metrics", () => {
  const testData = {
    consultationId: "test-consultation",
    loading: false,
    questions: [
      {
        id: "test-question-1-id",
        number: 1,
        total_responses: 10,
        question_text: "Test question 1 text",
        slug: "test-question-1-slug",
        has_free_text: false,
        has_multiple_choice: true,
        multiple_choice_answer: [
          {
            id: "multi-answer-1",
            text: "Multi Answer 1",
            response_count: 10,
          },
          {
            id: "multi-answer-2",
            text: "Multi Answer 2",
            response_count: 20,
          },
        ],
        proportion_of_audited_answers: 0,
      },
    ],
    demoOptions: [
      {
        id: "1",
        name: "Demo Option Category 1",
        value: "Category 1 Demo Option 1",
        count: 100,
      },
      {
        id: "2",
        name: "Demo Option Category 1",
        value: "Category 1 Demo Option 2",
        count: 200,
      },
      {
        id: "3",
        name: "Demo Option Category 2",
        value: "Category 2 Demo Option 1",
        count: 300,
      },
      {
        id: "4",
        name: "Demo Option Category 2",
        value: "Category 2 Demo Option 2",
        count: 400,
      },
    ],
    demoOptionsLoading: false,
  };

  it("should not render chart if no question has multi answers", () => {
    render(Metrics, {
      ...testData,
      questions: testData.questions.map((question) => ({
        ...question,
        has_multiple_choice: false,
        multiple_choice_answer: [],
      })),
    });
    expect(screen.queryByTestId("metrics-chart")).toBeNull();
  });

  it("should render chart if some questions have multi answers", () => {
    render(Metrics, testData);
    expect(screen.getByTestId("metrics-chart")).toBeInTheDocument();
  });

  it("should render demo options data", () => {
    render(Metrics, testData);

    expect(screen.getByText("Demographics Breakdown")).toBeInTheDocument();

    testData.demoOptions.forEach((opt) => {
      expect(screen.getByText(opt.name)).toBeInTheDocument();
      expect(screen.getByText(opt.value)).toBeInTheDocument();
      expect(screen.getByText(opt.count)).toBeInTheDocument();
    });
  });

  it("should not render demo options section if no data", () => {
    render(Metrics, {
      ...testData,
      demoOptions: [],
    });
    expect(screen.queryByText("Demographics Breakdown")).toBeNull();
  });
});
