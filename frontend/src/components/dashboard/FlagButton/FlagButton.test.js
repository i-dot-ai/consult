import { afterEach, beforeEach, describe, expect, it, test, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { render, cleanup, screen } from "@testing-library/svelte";

import FlagButton from "./FlagButton.svelte";

let testData;

describe("FlagButton", () => {
  beforeEach(() => {
    testData = {
      consultationId: "test-consultation",
      questionId: "test-question",
      answerId: "test-answer",
    };
  });

  afterEach(() => cleanup());

  it("should call funcs with correct params", async () => {
    const user = userEvent.setup();
    const toggleFlagMock = vi.fn();
    const resetDataMock = vi.fn();

    render(FlagButton, {
      consultationId: testData.consultationId,
      questionId: testData.questionId,
      answerId: testData.answerId,
      isFlagged: false,
      toggleFlagMock: toggleFlagMock,
      resetData: resetDataMock,
    });

    const button = screen.getByRole("button");
    await user.click(button);

    expect(toggleFlagMock).toHaveBeenCalledWith(
      `/api/consultations/${testData.consultationId}/questions/${testData.questionId}/responses/${testData.answerId}/toggle-flag/`,
      "PATCH",
    );
    expect(resetDataMock).toHaveBeenCalledOnce();
  });

  it("should have aria pressed false if not flagged", async () => {
    const user = userEvent.setup();

    render(FlagButton, {
      consultationId: testData.consultationId,
      questionId: testData.questionId,
      answerId: testData.answerId,
      isFlagged: false,
    });

    const button = screen.getByRole("button");
    expect(button.getAttribute("aria-pressed")).toEqual("false");
  });

  it("should have aria pressed true if flagged", async () => {
    const user = userEvent.setup();

    render(FlagButton, {
      consultationId: testData.consultationId,
      questionId: testData.questionId,
      answerId: testData.answerId,
      isFlagged: true,
    });

    const button = screen.getByRole("button");
    expect(button.getAttribute("aria-pressed")).toEqual("true");
  });
});
