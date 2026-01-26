import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";

import QuestionSummary from "./QuestionSummary.svelte";
import { getPercentage } from "../../../global/utils";

describe("QuestionSummary", () => {
  const testData = {
    themesLoading: false,
    showThemes: false,
    demoData: { "testCategory": { "foo": 1 } },
    totalAnswers: 100,
    themes: [],
    demoOptions: { "testCategory": [ "foo" ] },
    anyFilterApplied: false,
    setActiveTab: () => {},
  };

  it("should render data", () => {
    render(QuestionSummary, {});

    expect(screen.getByText("Theme analysis")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Analysis of key themes mentioned in responses to this question.",
      ),
    ).toBeInTheDocument();
  });

  it("should render multi choice data if passed", () => {
    const multiChoice = [
      { id: "1", text: "yes", response_count: 10 },
      { id: "2", text: "no", response_count: 20 },
    ];

    render(QuestionSummary, {
      ...testData,
      multiChoice: multiChoice,
    });

    expect(screen.getByText("Multiple Choice Answers")).toBeInTheDocument();

    multiChoice.forEach((item) => {
      expect(screen.getByText(item.text)).toBeInTheDocument();
      expect(screen.getAllByText(item.response_count)).toHaveLength(2);
      expect(
        screen.getByText(getPercentage(item.response_count, 30) + "%"),
      ).toBeInTheDocument();
    });
  });
});
