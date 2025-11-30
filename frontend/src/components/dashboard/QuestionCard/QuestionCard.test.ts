import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";

import QuestionCard from "./QuestionCard.svelte";
describe("QuestionCard", () => {
  const testData = {
    consultationId: "test-consultation",
    question: {
      id: "test-question",
      number: 1,
      total_responses: 100,
      question_text: "Test question text",
    },
    // horizontal: false,
  };

  it("should render data", () => {
    render(QuestionCard, {
      consultationId: testData.consultationId,
      question: testData.question,
    });

    expect(
      screen.getByText(
        `Q${testData.question.number}: ${testData.question.question_text}`,
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(`${testData.question.total_responses} responses`),
    ).toBeInTheDocument();
    expect(screen.getByTestId("question-icon")).toBeInTheDocument();
    expect(screen.getByTestId("fav-button")).toBeInTheDocument();
  });

  it("should highlight text if highlighted is passed", () => {
    const HIGHLIGHT_TEXT = "question";

    const { container } = render(QuestionCard, {
      consultationId: testData.consultationId,
      question: testData.question,
      highlightText: HIGHLIGHT_TEXT,
    });

    const highlightedText = container.querySelector("span.bg-yellow-300");
    expect(highlightedText).toBeTruthy();
    expect(highlightedText?.innerHTML).toEqual(HIGHLIGHT_TEXT);
  });

  it("should render inside a tag if clickable is true", () => {
    render(QuestionCard, {
      consultationId: testData.consultationId,
      question: testData.question,
      clickable: true,
    });

    const questionButton = screen.getByTestId(
      `Click to view question: ${testData.question.question_text}`,
    );

    expect(questionButton.getAttribute("aria-label")).toEqual(
      `Click to view question: ${testData.question.question_text}`,
    );
    expect(questionButton.getAttribute("role")).toEqual("button");
    expect(questionButton.getAttribute("title")).toEqual(
      `Q${testData.question.number}: ${testData.question.question_text}`,
    );
  });

  it("should not render inside a tag if clickable is false", () => {
    render(QuestionCard, {
      consultationId: testData.consultationId,
      question: testData.question,
      clickable: false,
    });

    const questionButton = screen.queryByTestId(
      `Click to view question: ${testData.question.question_text}`,
    );
    expect(questionButton).toBeNull();
  });

  it("should not render icon if hideIcon is true", () => {
    render(QuestionCard, {
      consultationId: testData.consultationId,
      question: testData.question,
      hideIcon: true,
    });

    expect(screen.queryByTestId("question-icon")).toBeNull();
  });

  it("should not render data if skeleton", () => {
    render(QuestionCard, {
      consultationId: testData.consultationId,
      question: testData.question,
      skeleton: true,
    });

    expect(
      screen.queryByText(
        `Q${testData.question.number}: ${testData.question.question_text}`,
      ),
    ).toBeNull();
    expect(
      screen.queryByText(`${testData.question.total_responses} responses`),
    ).toBeNull();
  });

  it("should render alternative css if horizontal", () => {
    render(QuestionCard, {
      consultationId: testData.consultationId,
      question: testData.question,
      horizontal: true,
    });

    expect(
      screen.getByTestId("horizontal-container").getAttribute("class"),
    ).toContain("justify-between");
  });
});
