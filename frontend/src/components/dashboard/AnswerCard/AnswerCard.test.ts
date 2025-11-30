import { describe, expect, it } from "vitest";
import { render } from "@testing-library/svelte";

import AnswerCard from "./AnswerCard.svelte";

describe("AnswerCard", () => {
  const testData = {
    consultationId: "consultation-id",
    answerId: "answer-id",
    respondentId: "respondent-id",
    respondentDisplayId: "respondent-display-id",
    text: "Test answer",
    demoData: ["demo 1", "demo 2"],
    multiAnswers: ["multi 1", "multi 2"],
    evidenceRich: true,
    themes: [
      { id: "theme-1", name: "theme 1", description: "desc 1" },
      { id: "theme-2", name: "theme 2", description: "desc 2" },
    ],
  };

  it("should render data", () => {
    const { getByText } = render(AnswerCard, {
      ...testData,
    });

    expect(
      getByText(`ID: ${testData.respondentDisplayId}`),
    ).toBeInTheDocument();
    expect(getByText(testData.text!)).toBeInTheDocument();
    testData.demoData!.forEach((data) =>
      expect(getByText(data)).toBeInTheDocument(),
    );
    testData.multiAnswers!.forEach((multi) =>
      expect(getByText(multi)).toBeInTheDocument(),
    );
    testData.themes!.forEach((theme) =>
      expect(getByText(theme.name)).toBeInTheDocument(),
    );
    expect(getByText("Evidence-rich")).toBeInTheDocument();
  });

  it("should not render data if skeleton", async () => {
    const { queryByText } = render(AnswerCard, {
      ...testData,
      skeleton: true,
    });

    expect(queryByText(`ID: ${testData.respondentDisplayId}`)).toBeNull();
    expect(queryByText(testData.text!)).toBeNull();
    expect(queryByText("Evidence-rich")).toBeNull();
    testData.themes!.forEach((theme) =>
      expect(queryByText(theme.name)).toBeNull(),
    );
    testData.multiAnswers!.forEach((multi) =>
      expect(queryByText(multi)).toBeNull(),
    );
    testData.demoData!.forEach((demo) => expect(queryByText(demo)).toBeNull());
  });

  it("should highlight text if passed", async () => {
    const HIGHLIGHT_TEXT = "answer";
    const { container } = render(AnswerCard, {
      ...testData,
      highlightText: HIGHLIGHT_TEXT,
    });

    expect(container?.querySelector("span.bg-yellow-300")?.innerHTML).toEqual(
      HIGHLIGHT_TEXT,
    );
  });
});
