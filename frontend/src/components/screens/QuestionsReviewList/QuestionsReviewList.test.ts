import { afterEach, describe, expect, it } from "vitest";
import { render, screen, waitFor } from "@testing-library/svelte";

import QuestionsReviewList from "./QuestionsReviewList.svelte";
import fetchMock from "fetch-mock";
import { queryClient } from "../../../global/queryClient";
import { mockRoute } from "../../../global/utils";
import { questionsData } from "./testData";
import {
  CONSULTATION_ID,
  showNextFetchErrorMock,
  showNextFreeTextErrorMock,
  showNextMock,
  showNextNoMoreErrorMock,
} from "./mocks";
import userEvent from "@testing-library/user-event";

const clearMocks = () => {
  fetchMock.unmockGlobal();
  fetchMock.removeRoutes();
  queryClient.resetQueries();
};

describe("QuestionsReviewList", () => {
  afterEach(() => {
    clearMocks();
  });

  it.each(questionsData)("should render all questions", async (question) => {
    mockRoute(showNextMock);

    render(QuestionsReviewList, {
      consultationId: CONSULTATION_ID,
      questions: questionsData,
    });

    await waitFor(() => {
      expect(screen.getByText(question.question_text)).toBeInTheDocument();
    });
  });

  it.each(questionsData)("should render percentages", async (question) => {
    mockRoute(showNextMock);

    render(QuestionsReviewList, {
      consultationId: CONSULTATION_ID,
      questions: questionsData,
    });

    await waitFor(() => {
      expect(
        screen.getByText(
          `${question.proportion_of_audited_answers * 100}% reviewed`,
        ),
      ).toBeInTheDocument();
    });
  });

  it("should render next response error", async () => {
    mockRoute(showNextFetchErrorMock);

    render(QuestionsReviewList, {
      consultationId: CONSULTATION_ID,
      questions: questionsData,
    });

    const user = userEvent.setup();
    await user.click(
      screen.getAllByRole("button", { name: "Show next" }).at(0)!,
    );

    await waitFor(() => {
      expect(
        screen.getByText("Failed to fetch next response. Please try again."),
      ).toBeInTheDocument();
    });
  });

  it("should render no more responses error", async () => {
    mockRoute(showNextNoMoreErrorMock);

    render(QuestionsReviewList, {
      consultationId: CONSULTATION_ID,
      questions: questionsData,
    });

    const user = userEvent.setup();
    await user.click(
      screen.getAllByRole("button", { name: "Show next" }).at(0)!,
    );

    await waitFor(() => {
      expect(
        screen.getByText("No more responses to review."),
      ).toBeInTheDocument();
    });
  });

  it("should render free text error", async () => {
    mockRoute(showNextFreeTextErrorMock);

    render(QuestionsReviewList, {
      consultationId: CONSULTATION_ID,
      questions: questionsData,
    });

    const user = userEvent.setup();
    await user.click(
      screen.getAllByRole("button", { name: "Show next" }).at(0)!,
    );

    await waitFor(() => {
      expect(
        screen.getByText("This question does not have free text responses."),
      ).toBeInTheDocument();
    });
  });

  it("should match snapshot initially", () => {
    mockRoute(showNextMock);

    const { container } = render(QuestionsReviewList, {
      consultationId: CONSULTATION_ID,
      questions: questionsData,
    });
    expect(container).toMatchSnapshot();
  });
});
