import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { render, cleanup } from "@testing-library/svelte";

import AnswerCard, { type Props } from "./AnswerCard.svelte";

let testData: Props;

describe("AnswerCard", () => {
  beforeEach(() => {
    testData = {
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
  });

  afterEach(() => cleanup());

  it("should render data", () => {
    const { getByText } = render(AnswerCard, {
      ...testData,
    });

    expect(getByText(`ID: ${testData.respondentDisplayId}`));
    expect(getByText(testData.text!));
    testData.demoData!.forEach((data) => expect(getByText(data)));
    testData.multiAnswers!.forEach((multi) => expect(getByText(multi)));
    testData.themes!.forEach((theme) => expect(getByText(theme.name)));
    expect(getByText("Evidence-rich"));
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
