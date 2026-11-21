import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { render, screen, waitFor } from "@testing-library/svelte";

import ConsultationAnalysis from "./ConsultationAnalysis.svelte";
import fetchMock from "fetch-mock";
import { mockRoute } from "../../../global/utils";
import { queryClient } from "../../../global/queryClient";
import {
  consultationMock,
  questionsMock,
  demoOptionsMock,
  consultationV2Mock,
  v2QuestionsMock,
  v2DemoOptionsMock,
} from "./mocks";

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
  beforeEach(() => {
    // Vitest loads PUBLIC_* vars from the repo .env files — pin the flag off
    // explicitly so this suite exercises the v1 data sources.
    process.env.PUBLIC_DATA_SETUP_V2_ENABLED = "false";
  });

  afterEach(() => {
    delete process.env.PUBLIC_DATA_SETUP_V2_ENABLED;
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

  it("should display no demo data message when no demo data present", async () => {
    setupMocks();

    render(ConsultationAnalysis);

    await waitFor(() => {
      expect(screen.getByText("No demographics found")).toBeInTheDocument();
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

describe("ConsultationAnalysis (V2 flag enabled)", () => {
  beforeEach(() => {
    process.env.PUBLIC_DATA_SETUP_V2_ENABLED = "true";
  });

  afterEach(() => {
    delete process.env.PUBLIC_DATA_SETUP_V2_ENABLED;
    clearMocks();
  });

  it("renders v2 demographics and multiple choice charts behind the flag", async () => {
    [consultationV2Mock, v2QuestionsMock, v2DemoOptionsMock].forEach((mock) =>
      mockRoute(mock),
    );

    render(ConsultationAnalysis, { consultationId: "test-consultation" });

    await waitFor(() => {
      expect(screen.getByText("Nation")).toBeInTheDocument();
      expect(screen.getByText("Wales")).toBeInTheDocument();
    });
    await waitFor(() => {
      expect(screen.getByText("Multiple Choice Questions")).toBeInTheDocument();
      expect(
        screen.getAllByText(questionsMock.body.results[0].question_text, {
          exact: false,
        }).length,
      ).toBeGreaterThan(0);
    });
  });
});
