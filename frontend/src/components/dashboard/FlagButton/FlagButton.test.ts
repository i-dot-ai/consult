import { describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { render, screen } from "@testing-library/svelte";

import FlagButton from "./FlagButton.svelte";

describe("FlagButton", () => {
  const toggleFlagMock = vi.fn();
  const resetDataMock = vi.fn();
  const testData = {
    consultationId: "test-consultation",
    questionId: "test-question",
    answerId: "test-answer",
    toggleFlagMock: toggleFlagMock,
    resetData: resetDataMock,
  };

  it("should call funcs with correct params", async () => {
    const user = userEvent.setup();

    render(FlagButton, { ...testData, isFlagged: false });

    const button = screen.getByRole("button");
    await user.click(button);

    expect(toggleFlagMock).toHaveBeenCalledWith(
      `/api/consultations/${testData.consultationId}/responses/${testData.answerId}/toggle-flag/`,
      "PATCH",
    );
    expect(resetDataMock).toHaveBeenCalledOnce();
  });

  it("should have aria pressed false if not flagged", async () => {
    render(FlagButton, { ...testData, isFlagged: false });

    const button = screen.getByRole("button");
    expect(button.getAttribute("aria-pressed")).toEqual("false");
  });

  it("should have aria pressed true if flagged", async () => {
    render(FlagButton, { ...testData, isFlagged: true });

    const button = screen.getByRole("button");
    expect(button.getAttribute("aria-pressed")).toEqual("true");
  });
});
