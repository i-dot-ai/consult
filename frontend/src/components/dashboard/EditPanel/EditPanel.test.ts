import { describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { render, screen } from "@testing-library/svelte";

import EditPanel from "./EditPanel.svelte";

describe("EditPanel", () => {
  const testData = {
    consultationId: "test-consultation-id",
    questionId: "test-question-id",
    answerId: "test-answer-id",
    themes: [
      { id: "theme-one", name: "Theme 1", description: "Description 1" },
      { id: "theme-two", name: "Theme 2", description: "Description 2" },
    ],
    themeOptions: [],
    evidenceRich: false,
    resetData: () => {},
    setEditing: () => {},
  };

  it("should match snapshot", async () => {
    const { container } = render(EditPanel, testData);

    const button = screen.getByRole("button");
    ["aria-controls", "id"].forEach((attribute) => {
      // Confirm attribute is created
      expect(button?.getAttribute(attribute)).toBeTruthy();
      // Remove randomly generated attributes to avoid mismatch
      button?.removeAttribute(attribute);
    });

    expect(container).toMatchSnapshot();
  });

  it("should open and close on click and call setEditing callback", async () => {
    const setEditingMock = vi.fn();
    const user = userEvent.setup();

    render(EditPanel, {
      ...testData,
      setEditing: setEditingMock,
    });

    // Panel hidden initially
    expect(screen.queryByTestId("panel")).toBeNull();

    // Click to reveal panel
    const button = screen.getByRole("button");
    await user.click(button);

    expect(screen.getByTestId("panel")).toBeInTheDocument();
    expect(setEditingMock).toHaveBeenCalledWith(true);

    testData.themes.forEach((theme) => {
      expect(screen.getByText(theme.name)).toBeInTheDocument();
    });

    // Click again to close panel
    await user.click(button);
    expect(screen.queryByTestId("panel")).toBeNull();
    expect(setEditingMock).toHaveBeenCalledWith(false);
  });

  it("should update correct data and call resetData callback", async () => {
    const resetDataMock = vi.fn();
    const updateAnswerMock = vi.fn();
    const user = userEvent.setup();

    render(EditPanel, {
      ...testData,
      evidenceRich: true,
      resetData: resetDataMock,
      updateAnswerMock: updateAnswerMock,
    });

    // Click to reveal panel
    const button = screen.getByRole("button");
    await user.click(button);

    // Click to change evidence rich status
    const evidenceRichButton = screen.getByText("Not evidence-rich");
    await user.click(evidenceRichButton);

    // Click to save changes
    const saveButton = screen.getByText("Save Changes");
    await user.click(saveButton);

    // Correct endpoint is called with correct body
    expect(updateAnswerMock).toHaveBeenCalledWith({
      body: {
        evidenceRich: false,
        themes: testData.themes.map((theme) => ({
          id: theme.id,
        })),
      },
    });
    expect(resetDataMock).toHaveBeenCalledOnce();
  });
});
