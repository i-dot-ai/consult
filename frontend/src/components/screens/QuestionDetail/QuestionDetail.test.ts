import { afterEach, describe, expect, it } from "vitest";
import { render, screen, waitFor } from "@testing-library/svelte";

import QuestionDetail from "./QuestionDetail.svelte";
import fetchMock from "fetch-mock";
import { queryClient } from "../../../global/queryClient";
import { mockRoute } from "../../../global/utils";
import { CONSULTATION_ID, mocks, QUESTION_ID } from "./mocks";
import userEvent from "@testing-library/user-event";


const setupMocks = () => {
  Object.values(mocks).forEach(mock => mockRoute(mock));
}

const clearMocks = () => {
  fetchMock.unmockGlobal();
  fetchMock.removeRoutes();
  queryClient.resetQueries();
}

describe("EditUser", () => {
  afterEach(() => {
    clearMocks();
  })

  it("should render question", async () => {
    setupMocks();

    render(QuestionDetail, { consultationId: CONSULTATION_ID, questionId: QUESTION_ID });
    await waitFor(() => {
      expect(screen.getByText(mocks.questionMock.body.question_text, { exact: false })).toBeInTheDocument();
    })
  });

  it.each(mocks.themesMock.body().themes)("should render themes", async (theme) => {
    setupMocks();

    render(QuestionDetail, { consultationId: CONSULTATION_ID, questionId: QUESTION_ID });
    await waitFor(() => {
      expect(screen.getByText(theme.name)).toBeInTheDocument();
      expect(screen.getByText(theme.description)).toBeInTheDocument();
    })
  });
});
