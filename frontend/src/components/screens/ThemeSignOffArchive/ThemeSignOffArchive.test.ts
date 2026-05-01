import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/svelte";

import ThemeSignOffArchive from "./ThemeSignOffArchive.svelte";
import fetchMock from "fetch-mock";
import { queryClient } from "../../../global/queryClient";
import { mockRoute } from "../../../global/utils";
import { CONSULTATION_ID, consultationMock, consultationUpdateMock, questionsAllSignedOffMock, questionsMock } from "./mocks";
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

describe("ThemeSignOffArchive", () => {
  beforeEach(() => {
    clearMocks();
  });

  it.each(questionsMock.body.results)(
    "should render questions",
    async (question) => {
      setupMocks();

      render(ThemeSignOffArchive, {
        consultationId: CONSULTATION_ID,
      });

      await waitFor(() => {
        expect(screen.getByText(question.question_text, { exact: false })).toBeInTheDocument();
      });
    },
  );

  it(
    "should display signed off tag if questions are signed off",
    async () => {
      mockRoute(consultationMock);
      mockRoute(questionsAllSignedOffMock);

      render(ThemeSignOffArchive, {
        consultationId: CONSULTATION_ID,
      });

      await waitFor(() => {
        expect(screen.getAllByText("Signed off").length).toEqual(questionsAllSignedOffMock.body.results.length);
      });
    },
  );

  it(
    "should trigger mapping if confirm button is pressed",
    async () => {
      const mockedUpdate = {
        ...consultationUpdateMock,
        body: vi.fn(),
      };
      mockRoute(consultationMock);
      mockRoute(questionsAllSignedOffMock);
      mockRoute(mockedUpdate);

      render(ThemeSignOffArchive, {
        consultationId: CONSULTATION_ID,
      });

      await waitFor(() => {
        expect(screen.getAllByText("Signed off").length).toBeGreaterThan(0);
      });

      const confirmButton = screen.getByRole("button", { name: "Confirm and Proceed to Mapping" });
      const user = userEvent.setup();

      await user.click(confirmButton);

      await waitFor(() => {
        expect(screen.getByText("Confirm AI Mapping")).toBeInTheDocument();
      })

      const modalConfirmButton = screen.getByRole("button", { name: "Yes, Start AI Mapping" });
      await user.click(modalConfirmButton);

      await waitFor(() => {
        expect(mockedUpdate.body).toHaveBeenCalled();
      })
    },
  );

  it("should match snapshot initially", () => {
    setupMocks();

    const { container } = render(ThemeSignOffArchive, {
      consultationId: CONSULTATION_ID,
    });
    expect(container).toMatchSnapshot();
  });

  it("should match snapshot after loading", async () => {
    setupMocks();

    const { container } = render(ThemeSignOffArchive, {
      consultationId: CONSULTATION_ID,
    });

    await waitFor(() => {
      expect(
        screen.getByText(questionsMock.body.results[0].question_text, { exact: false }),
      ).toBeInTheDocument();
    });
    expect(container).toMatchSnapshot();
  });
});
