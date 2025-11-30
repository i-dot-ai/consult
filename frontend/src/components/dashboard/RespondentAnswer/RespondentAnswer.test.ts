import { describe, expect, it, vi } from "vitest";
import { render } from "@testing-library/svelte";

import RespondentAnswer from "./RespondentAnswer.svelte";
import RespondentAnswerStory from "./RespondentAnswerStory.svelte";

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
    vi.mock("svelte/transition");

    const { getByText } = render(RespondentAnswer, {
      ...testData,
    });

    expect(getByText(testData.questionTitle));
    expect(getByText(`Q${testData.questionNumber}`));
    expect(getByText(testData.answerText));
    testData.multiChoice.forEach((multiAnswer) =>
      expect(getByText(multiAnswer)),
    );
    testData.themes.forEach((theme) => expect(getByText(theme)));
    expect(getByText("Evidence-rich"));
  });

  it("should not fail if no themes presenet", () => {
    vi.mock("svelte/transition");

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

  it("should render story", () => {
    render(RespondentAnswerStory);
  });
});
