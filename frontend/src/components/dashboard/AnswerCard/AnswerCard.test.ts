import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";

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
    render(AnswerCard, {
      ...testData,
    });

    expect(
      screen.getByText(`ID: ${testData.respondentDisplayId}`),
    ).toBeInTheDocument();
    expect(screen.getByText(testData.text!)).toBeInTheDocument();
    testData.demoData!.forEach((data) =>
      expect(screen.getByText(data)).toBeInTheDocument(),
    );
    testData.multiAnswers!.forEach((multi) =>
      expect(screen.getByText(multi)).toBeInTheDocument(),
    );
    testData.themes!.forEach((theme) =>
      expect(screen.getByText(theme.name)).toBeInTheDocument(),
    );
    expect(screen.getByText("Evidence-rich")).toBeInTheDocument();
  });

  it("should not render data if skeleton", async () => {
    render(AnswerCard, {
      ...testData,
      skeleton: true,
    });

    expect(
      screen.queryByText(`ID: ${testData.respondentDisplayId}`),
    ).toBeNull();
    expect(screen.queryByText(testData.text!)).toBeNull();
    expect(screen.queryByText("Evidence-rich")).toBeNull();
    testData.themes!.forEach((theme) =>
      expect(screen.queryByText(theme.name)).toBeNull(),
    );
    testData.multiAnswers!.forEach((multi) =>
      expect(screen.queryByText(multi)).toBeNull(),
    );
    testData.demoData!.forEach((demo) =>
      expect(screen.queryByText(demo)).toBeNull(),
    );
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
