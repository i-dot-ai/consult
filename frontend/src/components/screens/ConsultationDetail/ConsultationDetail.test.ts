import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { render, screen, waitFor } from "@testing-library/svelte";

import ConsultationDetail from "./ConsultationDetail.svelte";
import fetchMock from "fetch-mock";
import { mockRoute } from "../../../global/utils";
import { queryClient } from "../../../global/queryClient";
import {
  CONSULTATION_ID,
  defaultQuestionsMock,
  demoOptionsMock,
  v2DemoOptionsMock,
  v2QuestionsMock,
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
  beforeEach(() => {
    // Vitest loads PUBLIC_* vars from the repo .env files — pin the flag off
    // explicitly so this suite exercises the v1 data sources.
    process.env.PUBLIC_DATA_SETUP_V2_ENABLED = "false";
  });

  afterEach(() => {
    delete process.env.PUBLIC_DATA_SETUP_V2_ENABLED;
    clearMocks();
  });

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

describe("ConsultationDetail (V2 flag enabled)", () => {
  beforeEach(() => {
    process.env.PUBLIC_DATA_SETUP_V2_ENABLED = "true";
  });

  afterEach(() => {
    delete process.env.PUBLIC_DATA_SETUP_V2_ENABLED;
    clearMocks();
  });

  it("renders questions and demographic options from the v2 API", async () => {
    [v2QuestionsMock, v2DemoOptionsMock].forEach((mock) => mockRoute(mock));

    render(ConsultationDetail, { consultationId: CONSULTATION_ID });

    await waitFor(() => {
      expect(
        screen.getAllByText(v2QuestionsMock.body[0].text, { exact: false })
          .length,
      ).toBeGreaterThan(0);
    });
    await waitFor(() => {
      expect(screen.getByText("Nation")).toBeInTheDocument();
      expect(screen.getByText("Age")).toBeInTheDocument();
    });
  });
});
