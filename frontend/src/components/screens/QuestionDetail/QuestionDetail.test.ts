import { afterEach, describe, expect, it } from "vitest";
import { render, screen, waitFor } from "@testing-library/svelte";

import QuestionDetail from "./QuestionDetail.svelte";
import fetchMock from "fetch-mock";
import { queryClient } from "../../../global/queryClient";
import { mockRoute } from "../../../global/utils";
import { responses, CONSULTATION_ID, mocks, QUESTION_ID } from "./mocks";
import userEvent from "@testing-library/user-event";

const setupMocks = () => {
  Object.values(mocks).forEach((mock) => mockRoute(mock));
};

const clearMocks = () => {
  fetchMock.unmockGlobal();
  fetchMock.removeRoutes();
  queryClient.resetQueries();
};

describe("QuestionDetail", () => {
  afterEach(() => {
    clearMocks();
  });

  it("should render question", async () => {
    setupMocks();

    render(QuestionDetail, {
      consultationId: CONSULTATION_ID,
      questionId: QUESTION_ID,
    });
    await waitFor(() => {
      expect(
        screen.getByText(mocks.questionMock.body.question_text, {
          exact: false,
        }),
      ).toBeInTheDocument();
    });
  });

  it.each(mocks.themesMock.body().themes)(
    "should render themes",
    async (theme) => {
      setupMocks();

      render(QuestionDetail, {
        consultationId: CONSULTATION_ID,
        questionId: QUESTION_ID,
      });
      await waitFor(() => {
        expect(screen.getByText(theme.name)).toBeInTheDocument();
        expect(screen.getByText(theme.description)).toBeInTheDocument();
      });
    },
  );

  it.each([
    ...new Set(
      responses.reduce(
        (acc, curr) => [...acc, ...(curr.multiple_choice_answer || [])],
        [] as Array<string>,
      ),
    ),
  ] as string[])("should render multi answers", async (multiAnswer) => {
    setupMocks();

    render(QuestionDetail, {
      consultationId: CONSULTATION_ID,
      questionId: QUESTION_ID,
    });
    await waitFor(() => {
      expect(screen.getByText(multiAnswer)).toBeInTheDocument();
    });
  });

  it("switches to response analysis tab when button is clicked", async () => {
    setupMocks();

    render(QuestionDetail, {
      consultationId: CONSULTATION_ID,
      questionId: QUESTION_ID,
    });

    // page loaded
    await waitFor(() => {
      expect(
        screen.getByText(mocks.questionMock.body.question_text, {
          exact: false,
        }),
      ).toBeInTheDocument();
    });

    const responseAnalysisButton = screen.getByRole("tab", {
      name: "Response Analysis",
    });
    const user = userEvent.setup();

    await user.click(responseAnalysisButton);

    await waitFor(() => {
      expect(screen.getByText("Response refinement")).toBeInTheDocument();
    });
  });

  it.each(
    responses.filter((response) => Boolean(response.free_text_answer_text)),
  )("renders all responses", async (response) => {
    setupMocks();

    render(QuestionDetail, {
      consultationId: CONSULTATION_ID,
      questionId: QUESTION_ID,
    });

    // page loaded
    await waitFor(() => {
      expect(
        screen.getByText(mocks.questionMock.body.question_text, {
          exact: false,
        }),
      ).toBeInTheDocument();
    });

    const responseAnalysisButton = screen.getByRole("tab", {
      name: "Response Analysis",
    });
    const user = userEvent.setup();

    await user.click(responseAnalysisButton);

    await waitFor(() => {
      expect(
        screen.getByText(response.free_text_answer_text),
      ).toBeInTheDocument();
    });
  });

  it("adds/removes theme filter when buttons are clicked", async () => {
    setupMocks();

    render(QuestionDetail, {
      consultationId: CONSULTATION_ID,
      questionId: QUESTION_ID,
    });

    // page loaded
    await waitFor(() => {
      expect(screen.getByText("Standardized framework")).toBeInTheDocument();
    });

    const themeButton = screen.getByRole("button", {
      name: /Standardized framework/,
    });
    const user = userEvent.setup();

    await user.click(themeButton);

    await waitFor(() => {
      expect(screen.getByText("Selected Themes (1)")).toBeInTheDocument();
      expect(screen.getByText("Results are filtered")).toBeInTheDocument();
    });

    const removeButton = screen.getByRole("button", {
      name: "Remove theme filter for Standardized framework",
    });
    await user.click(removeButton);

    await waitFor(() => {
      expect(
        screen.queryByText("Selected Themes", { exact: false }),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByText("Results are filtered"),
      ).not.toBeInTheDocument();
    });
  });

  it("hybrid question uses correct counts for each section", async () => {
    setupMocks();

    render(QuestionDetail, {
      consultationId: CONSULTATION_ID,
      questionId: QUESTION_ID,
    });

    await waitFor(() => {
      expect(
        screen.getByText(mocks.questionMock.body.question_text, {
          exact: false,
        }),
      ).toBeInTheDocument();
    });

    // Top header shows total_response_count (250)
    expect(
      screen.getByText(
        `${mocks.questionMock.body.total_response_count} responses`,
      ),
    ).toBeInTheDocument();

    // Multi-choice section uses multi_choice_response_count
    expect(
      screen.getByText(
        `${mocks.questionMock.body.multi_choice_response_count} responses`,
      ),
    ).toBeInTheDocument();

    // Theme percentages use free_text_response_count (100) as denominator (62/100 = 62%)
    await waitFor(() => {
      expect(screen.getByText("62%")).toBeInTheDocument();
    });
  });

  it("should match snapshot initially", () => {
    setupMocks();

    const { container } = render(QuestionDetail, {
      consultationId: CONSULTATION_ID,
      questionId: QUESTION_ID,
    });
    expect(container).toMatchSnapshot();
  });

  it("should match snapshot after loading", async () => {
    setupMocks();

    const { container } = render(QuestionDetail, {
      consultationId: CONSULTATION_ID,
      questionId: QUESTION_ID,
    });

    await waitFor(() => {
      expect(
        screen.getByText(mocks.questionMock.body.question_text, {
          exact: false,
        }),
      ).toBeInTheDocument();
    });
    expect(container).toMatchSnapshot();
  });
});
