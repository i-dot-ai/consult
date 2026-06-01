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

  it("renders responses section after loading", async () => {
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

    await waitFor(() => {
      expect(screen.getByText("Free Text Responses")).toBeInTheDocument();
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
      expect(screen.getByText("Filtered")).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /Standardized framework/ }),
      ).toHaveAttribute("aria-pressed", "true");
    });

    await user.click(themeButton);

    await waitFor(() => {
      expect(screen.queryByText("Filtered")).not.toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /Standardized framework/ }),
      ).toHaveAttribute("aria-pressed", "false");
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

  it("sorts themes by count descending with generic themes pinned to bottom", async () => {
    setupMocks();

    render(QuestionDetail, {
      consultationId: CONSULTATION_ID,
      questionId: QUESTION_ID,
    });

    await waitFor(() => {
      expect(screen.getByText("Standardized framework")).toBeInTheDocument();
    });

    const expectedOrder = [
      "Standardized framework",
      "Test Theme",
      "No Reason Given",
      "Other",
    ];

    const themeElements = expectedOrder.map((name) => screen.getByText(name));

    for (let i = 0; i < themeElements.length - 1; i++) {
      expect(
        themeElements[i].compareDocumentPosition(themeElements[i + 1]) &
          Node.DOCUMENT_POSITION_FOLLOWING,
      ).toBeTruthy();
    }
  });
});
