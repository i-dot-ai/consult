import { describe, expect, it } from "vitest";
import { render } from "@testing-library/svelte";

import RespondentAnswer from "./RespondentAnswer.svelte";

describe("RespondentAnswer", () => {
  const testData = {
    consultationId: "123",
    questionId: "456",
    questionTitle:
      "Do you agree with the proposal to align the flavour categories of chocolate bars as outlined in the draft guidelines of the Chocolate Bar Regulation for the United Kingdom?",
    questionNumber: 1,
    answerText:
      "I agree in principle, but I think the guidelines should include a provision for periodic review to adapt to market changes.",
    multiChoice: ["multi 1", "multi 2"],
    themes: ["Innovation", "Standardized framework"],
    evidenceRich: true,
  };

  it("should render data", () => {
    const { getByText } = render(RespondentAnswer, {
      ...testData,
    });

    expect(getByText(testData.questionTitle)).toBeInTheDocument();
    expect(getByText(`Q${testData.questionNumber}`)).toBeInTheDocument();
    expect(getByText(testData.answerText)).toBeInTheDocument();
    testData.multiChoice.forEach((multiAnswer) =>
      expect(getByText(multiAnswer)).toBeInTheDocument(),
    );
    testData.themes.forEach((theme) =>
      expect(getByText(theme)).toBeInTheDocument(),
    );
    expect(getByText("Evidence-rich")).toBeInTheDocument();
  });

  it("should not fail if no themes presenet", () => {
    expect(() => {
      render(RespondentAnswer, {
        ...testData,
        themes: [],
      });
    }).not.toThrow();
  });

  it("should not render evidence rich tag if not evidence rich", () => {
    const { queryByText } = render(RespondentAnswer, {
      ...testData,
      evidenceRich: false,
    });

    expect(queryByText("Evidence-rich")).toBeNull();
  });
});
