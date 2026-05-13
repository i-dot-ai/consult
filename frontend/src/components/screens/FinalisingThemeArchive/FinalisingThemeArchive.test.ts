import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/svelte";

import FinalisingThemeArchive from "./FinalisingThemeArchive.svelte";
import fetchMock from "fetch-mock";
import { queryClient } from "../../../global/queryClient";
import { mockRoute } from "../../../global/utils";
import { getFinaliseThemesUrl } from "../../../global/routes";
import {
  CONSULTATION_ID,
  consultationMock,
  consultationUpdateMock,
  questionsAllSignedOffMock,
  questionsMock,
} from "./mocks";
import userEvent from "@testing-library/user-event";

const mocks = {
  consultationMock,
  consultationUpdateMock,
  questionsMock,
};

function setupMocks() {
  Object.values(mocks).forEach((mock) => mockRoute(mock));
}
function clearMocks() {
  fetchMock.unmockGlobal();
  fetchMock.removeRoutes();
  queryClient.resetQueries();
}

describe("FinalisingThemeArchive", () => {
  beforeEach(() => {
    clearMocks();
  });

  it.each(questionsMock.body.results)(
    "should render questions",
    async (question) => {
      setupMocks();

      render(FinalisingThemeArchive, {
        consultationId: CONSULTATION_ID,
      });

      await waitFor(() => {
        expect(
          screen.getByText(question.question_text, { exact: false }),
        ).toBeInTheDocument();
      });
    },
  );

  it("should display signed off tag if questions are signed off", async () => {
    mockRoute(consultationMock);
    mockRoute(questionsAllSignedOffMock);

    render(FinalisingThemeArchive, {
      consultationId: CONSULTATION_ID,
    });

    await waitFor(() => {
      expect(screen.getAllByText("Signed off").length).toEqual(
        questionsAllSignedOffMock.body.results.length,
      );
    });
  });

  it("should trigger mapping if confirm button is pressed", async () => {
    const mockedUpdate = {
      url: getFinaliseThemesUrl(CONSULTATION_ID),
      method: "PATCH",
      body: vi.fn(() => ({ ...consultationMock.body, stage: "theme_mapping" })),
    };
    mockRoute(consultationMock);
    mockRoute(questionsAllSignedOffMock);
    mockRoute(mockedUpdate);

    render(FinalisingThemeArchive, {
      consultationId: CONSULTATION_ID,
    });

    await waitFor(() => {
      expect(screen.getAllByText("Signed off").length).toBeGreaterThan(0);
    });

    const confirmButton = screen.getByRole("button", {
      name: "Confirm and Proceed to Mapping",
    });
    const user = userEvent.setup();

    await user.click(confirmButton);

    await waitFor(() => {
      expect(screen.getByText("Confirm AI Mapping")).toBeInTheDocument();
    });

    const modalConfirmButton = screen.getByRole("button", {
      name: "Yes, Start AI Mapping",
    });
    await user.click(modalConfirmButton);

    await waitFor(() => {
      expect(mockedUpdate.body).toHaveBeenCalled();
    });
  });

  it("should render correct panel for analysis stage", async () => {
    mockRoute({
      ...consultationMock,
      body: {
        ...consultationMock.body,
        stage: "analysis",
      },
    });
    mockRoute(questionsAllSignedOffMock);

    render(FinalisingThemeArchive, {
      consultationId: CONSULTATION_ID,
    });

    await waitFor(() => {
      expect(screen.getByText("AI Assignment Complete")).toBeInTheDocument();
    });
  });

  it("should render correct panel for mapping stage", async () => {
    mockRoute({
      ...consultationMock,
      body: {
        ...consultationMock.body,
        stage: "theme_mapping",
      },
    });
    mockRoute(questionsAllSignedOffMock);

    render(FinalisingThemeArchive, {
      consultationId: CONSULTATION_ID,
    });

    await waitFor(() => {
      expect(screen.getByText("AI Assignment in Progress")).toBeInTheDocument();
    });
  });

  it("should render correct panel for sign off stage", async () => {
    mockRoute({
      ...consultationMock,
      body: {
        ...consultationMock.body,
        stage: "theme_sign_off",
      },
    });
    mockRoute(questionsMock);

    render(FinalisingThemeArchive, {
      consultationId: CONSULTATION_ID,
    });

    await waitFor(() => {
      expect(screen.getAllByText("Finalising Themes")).toHaveLength(2);
    });
  });

  it("should render correct panel for sign off stage all questions signed off", async () => {
    mockRoute({
      ...consultationMock,
      body: {
        ...consultationMock.body,
        stage: "theme_sign_off",
      },
    });
    mockRoute(questionsAllSignedOffMock);

    render(FinalisingThemeArchive, {
      consultationId: CONSULTATION_ID,
    });

    await waitFor(() => {
      expect(screen.getByText("All Questions Signed Off")).toBeInTheDocument();
    });
  });

  it("should match snapshot initially", () => {
    setupMocks();

    const { container } = render(FinalisingThemeArchive, {
      consultationId: CONSULTATION_ID,
    });
    expect(container).toMatchSnapshot();
  });

  it("should match snapshot after loading", async () => {
    setupMocks();

    const { container } = render(FinalisingThemeArchive, {
      consultationId: CONSULTATION_ID,
    });

    await waitFor(() => {
      expect(
        screen.getByText(questionsMock.body.results[0].question_text, {
          exact: false,
        }),
      ).toBeInTheDocument();
    });
    expect(container).toMatchSnapshot();
  });
});
