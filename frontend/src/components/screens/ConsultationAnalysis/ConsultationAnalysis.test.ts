import { afterEach, describe, expect, it } from "vitest";
import { render, screen, waitFor } from "@testing-library/svelte";

import ConsultationAnalysis from "./ConsultationAnalysis.svelte";
import fetchMock from "fetch-mock";
import { mockRoute } from "../../../global/utils";
import { queryClient } from "../../../global/queryClient";
import { consultationMock, questionsMock, demoOptionsMock } from "./mocks";

describe("ConsultationAnalysis", () => {
  afterEach(() => {
    fetchMock.unmockGlobal();
    fetchMock.removeRoutes();
    queryClient.resetQueries();
  });

  it.each(
    questionsMock.body.results.filter(
      (question) => question.has_multiple_choice,
    ),
  )("should render all folder options", async (question) => {
    [consultationMock, questionsMock, demoOptionsMock].forEach((mock) =>
      mockRoute(mock),
    );

    render(ConsultationAnalysis, { consultationId: "test-consultation" });

    await waitFor(() => {
      expect(
        screen.getAllByText(question.question_text).length,
      ).toBeGreaterThan(0);
    });
  });
});
