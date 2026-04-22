import { afterEach, describe, expect, it } from "vitest";
import { render, screen, waitFor } from "@testing-library/svelte";

import ThemeSignOffDetailCompleted from "./ThemeSignOffDetailCompleted.svelte";
import {
  CONSULTATION_ID,
  QUESTION_ID,
  questionMock,
  selectedThemesMock,
} from "./mocks";
import fetchMock from "fetch-mock";
import { mockRoute } from "../../../global/utils";
import { queryClient } from "../../../global/queryClient";

describe("ThemeSignOffDetailCompleted", () => {
  afterEach(() => {
    fetchMock.unmockGlobal();
    fetchMock.removeRoutes();
    queryClient.resetQueries();
  });

  it.each(selectedThemesMock.body.results)(
    "should render themes",
    async (theme) => {
      mockRoute(selectedThemesMock);
      mockRoute(questionMock);

      render(ThemeSignOffDetailCompleted, {
        consultationId: CONSULTATION_ID,
        questionId: QUESTION_ID,
      });

      await waitFor(() => {
        expect(screen.getByText(theme.name)).toBeInTheDocument();
      });
    },
  );

  it("should display error if selected themes query errors", async () => {
    mockRoute({ ...selectedThemesMock, status: 500, body: undefined });
    mockRoute(questionMock);

    render(ThemeSignOffDetailCompleted, {
      consultationId: CONSULTATION_ID,
      questionId: QUESTION_ID,
    });

    await waitFor(() => {
      expect(
        screen.getByText("Fetch Error:", { exact: false }),
      ).toBeInTheDocument();
    });
  });

  it("should match snapshot initially", () => {
    const { container } = render(ThemeSignOffDetailCompleted, {
      consultationId: CONSULTATION_ID,
      questionId: QUESTION_ID,
    });
    expect(container).toMatchSnapshot();
  });

  it("should match snapshot after loading", async () => {
    mockRoute(selectedThemesMock);
    mockRoute(questionMock);

    const { container } = render(ThemeSignOffDetailCompleted, {
      consultationId: CONSULTATION_ID,
      questionId: QUESTION_ID,
    });

    await waitFor(() => {
      expect(
        screen.getByText(selectedThemesMock.body.results[0].name),
      ).toBeInTheDocument();
    });
    expect(container).toMatchSnapshot();
  });
});
