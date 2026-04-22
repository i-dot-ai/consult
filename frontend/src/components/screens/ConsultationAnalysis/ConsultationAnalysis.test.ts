import { afterEach, describe, expect, it } from "vitest";
import { render, screen, waitFor } from "@testing-library/svelte";

import ConsultationAnalysis from "./ConsultationAnalysis.svelte";
import fetchMock from "fetch-mock";
import { mockRoute } from "../../../global/utils";
import { queryClient } from "../../../global/queryClient";
import { consultationMock, questionsMock, demoOptionsMock } from "./mocks";

function setupMocks() {
  [consultationMock, questionsMock, demoOptionsMock].forEach((mock) =>
    mockRoute(mock),
  );
}

function clearMocks() {
  fetchMock.unmockGlobal();
  fetchMock.removeRoutes();
  queryClient.resetQueries();
}

describe("ConsultationAnalysis", () => {
  afterEach(() => {
    clearMocks();
  });

  it.each(
    questionsMock.body.results.filter(
      (question) => question.has_multiple_choice,
    ),
  )("should render all folder options", async (question) => {
    setupMocks();

    render(ConsultationAnalysis, { consultationId: "test-consultation" });

    await waitFor(() => {
      expect(
        screen.getAllByText(question.question_text).length,
      ).toBeGreaterThan(0);
    });
  });

  it("should match snapshot initially", () => {
    setupMocks();

    const { container } = render(ConsultationAnalysis, {
      consultationId: "test-consultation",
    });
    expect(container).toMatchSnapshot();
  });

  it("should match snapshot after loading", async () => {
    setupMocks();

    const { container } = render(ConsultationAnalysis, {
      consultationId: "test-consultation",
    });

    await waitFor(() => {
      expect(
        screen.getAllByText(questionsMock.body.results[0].question_text, {
          exact: false,
        }).length,
      ).toBeGreaterThan(0);
    });
    expect(container).toMatchSnapshot();
  });
});
