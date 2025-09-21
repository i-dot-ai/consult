import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { render, cleanup } from "@testing-library/svelte";

import EditPanel from "./EditPanel.svelte";

let testData;

describe("EditPanel", () => {
  beforeEach(() => {
    testData = {
      consultationId: "test-consultation-id",
      questionId: "test-question-id",
      answerId: "test-answer-id",
      themes: [
        { id: "theme-one", name: "Theme 1" },
        { id: "theme-two", name: "Theme 2" },
      ],
      themeOptions: [],
      evidenceRich: false,
      resetData: () => {},
      setEditing: () => {},
    };
  });

  afterEach(() => cleanup());

  it("should open and close on click and call setEditing callback", async () => {
    vi.mock("svelte/transition");
    const setEditingMock = vi.fn();
    const user = userEvent.setup();

    const { getByText, getByRole, getByTestId, queryByTestId } = render(
      EditPanel,
      {
        ...testData,
        setEditing: setEditingMock,
      },
    );

    // Panel hidden initially
    expect(queryByTestId("panel")).toBeNull();

    // Click to reveal panel
    const button = getByRole("button");
    await user.click(button);

    expect(getByTestId("panel"));
    expect(setEditingMock).toHaveBeenCalledWith(true);

    testData.themes.forEach((theme) => {
      getByText(theme.name);
    });

    // Click again to close panel
    await user.click(button);
    expect(queryByTestId("panel")).toBeNull();
    expect(setEditingMock).toHaveBeenCalledWith(false);
  });

  it("should update correct data and call resetData callback", async () => {
    vi.mock("svelte/transition");
    const resetDataMock = vi.fn();
    const updateAnswerMock = vi.fn();
    const user = userEvent.setup();

    const { getByText, getByRole } = render(EditPanel, {
      ...testData,
      evidenceRich: true,
      resetData: resetDataMock,
      updateAnswerMock: updateAnswerMock,
    });

    // Click to reveal panel
    const button = getByRole("button");
    await user.click(button);

    // Click to change evidence rich status
    const evidenceRichButton = getByText("Not evidence-rich");
    await user.click(evidenceRichButton);

    // Click to save changes
    const saveButton = getByText("Save Changes");
    await user.click(saveButton);

    // Correct endpoint is called with correct body
    expect(updateAnswerMock).toHaveBeenCalledWith(
      `/api/consultations/${testData.consultationId}/questions/${testData.questionId}/responses/${testData.answerId}/`,
      "PATCH",
      {
        evidenceRich: false,
        themes: testData.themes.map((theme) => ({
          id: theme.id,
        })),
      },
    );
    expect(resetDataMock).toHaveBeenCalledOnce();
  });
});
