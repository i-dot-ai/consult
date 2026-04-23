import { beforeEach, describe, expect, it } from "vitest";
import { render, screen, waitFor } from "@testing-library/svelte";

import RespondentDetail from "./RespondentDetail.svelte";
import fetchMock from "fetch-mock";
import { queryClient } from "../../../global/queryClient";
import { mockRoute } from "../../../global/utils";
import {
  CONSULTATION_ID,
  consultationQuestionsMock,
  QUESTION_ID,
  questionsMock,
  RESPONDENT_ID,
  respondentsMock,
  responsesMock,
  updateRespondentMock,
} from "./mocks";
import userEvent from "@testing-library/user-event";

const mocks = {
  consultationQuestionsMock,
  questionsMock,
  respondentsMock,
  responsesMock,
  updateRespondentMock,
};

function setupMocks() {
  Object.values(mocks).forEach((mock) => mockRoute(mock));
}
function clearMocks() {
  fetchMock.unmockGlobal();
  fetchMock.removeRoutes();
  queryClient.resetQueries();
}

describe("RespondentDetail", () => {
  beforeEach(() => {
    clearMocks();
  });

  it.each(consultationQuestionsMock.body.results)(
    "should render question title",
    async (question) => {
      setupMocks();

      render(RespondentDetail, {
        consultationId: CONSULTATION_ID,
        questionId: QUESTION_ID,
        respondentId: RESPONDENT_ID,
        themefinderId: 1,
      });

      await waitFor(() => {
        expect(
          screen.getAllByText(question.question_text, { exact: false }).length,
        ).toBeGreaterThan(0);
      });
    },
  );

  it("should update stakeholder name", async () => {
    setupMocks();

    render(RespondentDetail, {
      consultationId: CONSULTATION_ID,
      questionId: QUESTION_ID,
      respondentId: RESPONDENT_ID,
      themefinderId: 1,
    });

    const user = userEvent.setup();
    await user.click(screen.getByTestId("edit-button"));
    await user.type(screen.getByRole("textbox"), "test name");
    await user.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(
      () => {
        expect(screen.getByText("test name")).toBeInTheDocument();
      },
      { timeout: 10000 },
    );
  }, 10000);

  it("should match snapshot initially", () => {
    setupMocks();

    const { container } = render(RespondentDetail, {
      consultationId: CONSULTATION_ID,
      questionId: QUESTION_ID,
      respondentId: RESPONDENT_ID,
      themefinderId: 1,
    });
    expect(container).toMatchSnapshot();
  });

  it("should match snapshot after loading", async () => {
    setupMocks();

    const { container } = render(RespondentDetail, {
      consultationId: CONSULTATION_ID,
      questionId: QUESTION_ID,
      respondentId: RESPONDENT_ID,
      themefinderId: 1,
    });

    await waitFor(() => {
      expect(
        screen.getAllByText(
          consultationQuestionsMock.body.results[0].question_text,
          { exact: false },
        ).length,
      ).toBeGreaterThan(0);
    });
    expect(container).toMatchSnapshot();
  });
});
