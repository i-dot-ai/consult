import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/svelte";

import ThemeSelectionForm from "./ThemeSelectionForm.svelte";
import fetchMock from "fetch-mock";
import { queryClient } from "../../../global/queryClient";
import userEvent from "@testing-library/user-event";
import { CONSULTATION_ID, QUESTION_ID, RESPONSE_ID, showNextMock, submitMock } from "./mocks";
import { allThemes, selectedThemes } from "./testData";
import { mockRoute } from "../../../global/utils";


const clearMocks = () => {
  fetchMock.unmockGlobal();
  fetchMock.removeRoutes();
  queryClient.resetQueries();
};

const unselectedThemes = allThemes.filter(theme => selectedThemes.find(selectedTheme => selectedTheme.id !== theme.id));

describe("ThemeSelectionForm", () => {
  afterEach(() => {
    clearMocks();
  });

  it.each(allThemes)("should render all themes", async (theme) => {
    mockRoute(showNextMock);
    mockRoute(submitMock);

    render(ThemeSelectionForm, {
      consultationId: CONSULTATION_ID,
      questionId: QUESTION_ID,
      responseId: RESPONSE_ID,
      allThemes: allThemes,
      selectedThemes: selectedThemes,
    });
    await waitFor(() => {
      expect(
        screen.getByLabelText(theme.name),
      ).toBeInTheDocument();
    });
  });

  it.each(selectedThemes)("should initially select all selected themes", async (theme) => {
    mockRoute(showNextMock);
    mockRoute(submitMock);

    render(ThemeSelectionForm, {
      consultationId: CONSULTATION_ID,
      questionId: QUESTION_ID,
      responseId: RESPONSE_ID,
      allThemes: allThemes,
      selectedThemes: selectedThemes,
    });

    await waitFor(() => {
      const checkbox = screen.getByLabelText(theme.name);
      expect(
        checkbox,
      ).toBeChecked();
    });
  });

  it.each(unselectedThemes)("should initially not select any unselected themes", async (theme) => {
    mockRoute(showNextMock);
    mockRoute(submitMock);

    render(ThemeSelectionForm, {
      consultationId: CONSULTATION_ID,
      questionId: QUESTION_ID,
      responseId: RESPONSE_ID,
      allThemes: allThemes,
      selectedThemes: selectedThemes,
    });

    await waitFor(() => {
      const checkbox = screen.getByLabelText(theme.name);
      expect(
        checkbox,
      ).not.toBeChecked();
    });
  });

  it("should send request with themes selected when submitted", async () => {
    const submitMockCallback = vi.fn();

    mockRoute(showNextMock);
    mockRoute({
      ...submitMock,
      body: submitMockCallback,
    });

    render(ThemeSelectionForm, {
      consultationId: CONSULTATION_ID,
      questionId: QUESTION_ID,
      responseId: RESPONSE_ID,
      allThemes: allThemes,
      selectedThemes: selectedThemes,
    });

    const user = userEvent.setup();
    const submitButton = screen.getByRole("button", { name: "Save and continue to next response" });
    await user.click(submitButton);

    await waitFor(() => {
      expect(
        submitMockCallback,
      ).toHaveBeenCalledWith(
        expect.objectContaining({
          body: JSON.stringify({
            themes: selectedThemes,
            human_reviewed: true,
          })
        })
      );
    });
  });

  it("should send request to showNext when skipped", async () => {
    const showNextMockCallback = vi.fn();

    mockRoute(submitMock);
    mockRoute({
      ...showNextMock,
      body: showNextMockCallback,
    });

    render(ThemeSelectionForm, {
      consultationId: CONSULTATION_ID,
      questionId: QUESTION_ID,
      responseId: RESPONSE_ID,
      allThemes: allThemes,
      selectedThemes: selectedThemes,
    });

    const user = userEvent.setup();
    const submitButton = screen.getByRole("button", { name: "Skip this response" });
    await user.click(submitButton);

    await waitFor(() => {
      expect(
        showNextMockCallback,
      ).toHaveBeenCalled();
    });
  });

  it.each(selectedThemes)("should unselect theme when clicked", async (theme) => {
    mockRoute(showNextMock);
    mockRoute(submitMock);

    render(ThemeSelectionForm, {
      consultationId: CONSULTATION_ID,
      questionId: QUESTION_ID,
      responseId: RESPONSE_ID,
      allThemes: allThemes,
      selectedThemes: selectedThemes,
    });

    const checkbox = screen.getByLabelText(theme.name);
    expect(checkbox).toBeChecked();

    const user = userEvent.setup();
    await user.click(checkbox);

    await waitFor(() => {
      expect(checkbox).not.toBeChecked();
    });
  });

  it("should match snapshot initially", () => {
    mockRoute(showNextMock);
    mockRoute(submitMock);

    const { container } = render(ThemeSelectionForm, {
      consultationId: CONSULTATION_ID,
      questionId: QUESTION_ID,
      responseId: RESPONSE_ID,
      allThemes: allThemes,
      selectedThemes: selectedThemes,
    });
    expect(container).toMatchSnapshot();
  });
});
