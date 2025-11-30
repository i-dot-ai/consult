import { describe, expect, it } from "vitest";
import { render } from "@testing-library/svelte";

import QuestionSummary from "./QuestionSummary.svelte";
import { getPercentage } from "../../../global/utils";

describe("QuestionSummary", () => {
  const testData = {
    themesLoading: false,
  };

  it("should render data", () => {
    const { getByText } = render(QuestionSummary, {});

    expect(getByText("Theme analysis"));
    expect(
      getByText(
        "Analysis of key themes mentioned in responses to this question.",
      ),
    );
  });

  it("should render multi choice data if passed", () => {
    const multiChoice = [
      { text: "yes", response_count: 10 },
      { text: "no", response_count: 20 },
    ];

    const { getByText, getAllByText } = render(QuestionSummary, {
      multiChoice: multiChoice,
      themesLoading: testData.themesLoading,
    });

    expect(getByText("Multiple Choice Answers"));

    multiChoice.forEach((item) => {
      expect(getByText(item.text));
      expect(getAllByText(item.response_count));
      expect(getByText(getPercentage(item.response_count, 30) + "%"));
    });
  });
});
