import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { render, screen, waitFor } from "@testing-library/svelte";

import QuestionsReviewList from "./QuestionsReviewList.svelte";
import fetchMock from "fetch-mock";
import { queryClient } from "../../../global/queryClient";
import { mockRoute } from "../../../global/utils";
import type { Question } from "../../../global/types";
import { questionsData } from "./testData";
import {
  CONSULTATION_ID,
  showNextFetchErrorMock,
  showNextFreeTextErrorMock,
  showNextMock,
  showNextNoMoreErrorMock,
  showNextV2FreeTextErrorMock,
  showNextV2Mock,
  v2ClosedQuestion,
} from "./mocks";
import userEvent from "@testing-library/user-event";

const clearMocks = () => {
  fetchMock.unmockGlobal();
  fetchMock.removeRoutes();
  queryClient.resetQueries();
};

describe("QuestionsReviewList", () => {
  beforeEach(() => {
    // Vitest loads PUBLIC_* vars from the repo .env files — pin the flag off
    // explicitly so this suite exercises the v1 data sources.
    process.env.PUBLIC_DATA_SETUP_V2_ENABLED = "false";
  });

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

describe("QuestionsReviewList (V2 flag enabled)", () => {
  beforeEach(() => {
    process.env.PUBLIC_DATA_SETUP_V2_ENABLED = "true";
  });

  afterEach(() => {
    delete process.env.PUBLIC_DATA_SETUP_V2_ENABLED;
    clearMocks();
  });

  it("gates by v2 question type and calls the v2 show-next endpoint", async () => {
    mockRoute(showNextV2FreeTextErrorMock);

    render(QuestionsReviewList, {
      consultationId: CONSULTATION_ID,
      questions: [v2ClosedQuestion as unknown as Question],
    });

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "Show next" }));

    await waitFor(() => {
      expect(
        screen.getByText("This question does not have free text responses."),
      ).toBeInTheDocument();
    });
  });

  it("finds the next response via the v2 endpoint for open questions", async () => {
    mockRoute(showNextV2Mock);

    render(QuestionsReviewList, {
      consultationId: CONSULTATION_ID,
      questions: [v2ClosedQuestion as unknown as Question],
    });

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "Show next" }));

    await waitFor(() => {
      const v2Calls = fetchMock.callHistory
        .calls()
        .filter(
          (call) =>
            call.url.includes("/api/v2") && call.url.includes("show-next"),
        );
      expect(v2Calls.length).toBeGreaterThan(0);
    });
  });
});
