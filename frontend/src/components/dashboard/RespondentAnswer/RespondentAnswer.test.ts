import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";

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
    render(RespondentAnswer, {
      ...testData,
    });

    expect(screen.getByText(testData.questionTitle)).toBeInTheDocument();
    expect(screen.getByText(`Q${testData.questionNumber}`)).toBeInTheDocument();
    expect(screen.getByText(testData.answerText)).toBeInTheDocument();
    testData.multiChoice.forEach((multiAnswer) =>
      expect(screen.getByText(multiAnswer)).toBeInTheDocument(),
    );
    testData.themes.forEach((theme) =>
      expect(screen.getByText(theme)).toBeInTheDocument(),
    );
    expect(screen.getByText("Evidence-rich")).toBeInTheDocument();
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
    render(RespondentAnswer, {
      ...testData,
      evidenceRich: false,
    });

    expect(screen.queryByText("Evidence-rich")).toBeNull();
  });
});
