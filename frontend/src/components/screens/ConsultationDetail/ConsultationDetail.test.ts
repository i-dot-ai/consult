import { afterEach, describe, expect, it } from "vitest";
import { render, screen, waitFor } from "@testing-library/svelte";

import ConsultationDetail from "./ConsultationDetail.svelte";
import fetchMock from "fetch-mock";
import { mockRoute } from "../../../global/utils";
import { queryClient } from "../../../global/queryClient";
import {
  CONSULTATION_ID,
  defaultQuestionsMock,
  demoOptionsMock,
} from "./mocks";

const setupMocks = () => {
  [defaultQuestionsMock, demoOptionsMock].forEach((mock) => mockRoute(mock));
};

const clearMocks = () => {
  fetchMock.unmockGlobal();
  fetchMock.removeRoutes();
  queryClient.resetQueries();
};

describe("ConsultationDetail", () => {
  afterEach(() => clearMocks());

  it.each(defaultQuestionsMock.body.results)(
    "should render all questions",
    async (question) => {
      setupMocks();

      render(ConsultationDetail, { consultationId: CONSULTATION_ID });

      await waitFor(() => {
        expect(
          screen.getAllByText(question.question_text, { exact: false }).length,
        ).toBeGreaterThan(0);
      });
    },
  );

  it("should match snapshot initially", () => {
    setupMocks();

    const { container } = render(ConsultationDetail, {
      consultationId: CONSULTATION_ID,
    });
    expect(container).toMatchSnapshot();
  });

  it("should match snapshot after loading", async () => {
    setupMocks();

    const { container } = render(ConsultationDetail, {
      consultationId: CONSULTATION_ID,
    });

    await waitFor(() => {
      expect(
        screen.getAllByText(
          defaultQuestionsMock.body.results[0].question_text,
          { exact: false },
        ).length,
      ).toBeGreaterThan(0);
    });
    expect(container).toMatchSnapshot();
  });
});
