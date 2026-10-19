import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/svelte";
import fetchMock from "fetch-mock";

import DeleteQuestionsPage from "./DeleteQuestionsPage.svelte";
import { CONSULTATION_ID, QUESTIONS, deleteMock, questionsMock } from "./mocks";
import { mockRoute } from "../../../global/utils";
import { queryClient } from "../../../global/queryClient";

describe("DeleteQuestionsPage", () => {
  const TEST_DATA = { consultationId: CONSULTATION_ID };

  beforeEach(() => {
    vi.stubGlobal("location", { href: "", origin: window.location.origin });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    fetchMock.unmockGlobal();
    fetchMock.removeRoutes();
    queryClient.resetQueries();
  });

  it("renders the step title", async () => {
    mockRoute(questionsMock);
    render(DeleteQuestionsPage, TEST_DATA);

    expect(screen.getByText("Step 4 of 6")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { level: 1, name: "Delete questions" }),
    ).toBeInTheDocument();
  });

  it("renders the question list after loading", async () => {
    mockRoute(questionsMock);
    render(DeleteQuestionsPage, TEST_DATA);

    await waitFor(() => {
      expect(screen.getByText("Response ID")).toBeInTheDocument();
    });

    expect(screen.getByText("Start date")).toBeInTheDocument();
    expect(
      screen.getByText("What is your respondent type?"),
    ).toBeInTheDocument();
    expect(screen.getByText("3 questions")).toBeInTheDocument();
  });

  it("shows loading state initially", () => {
    mockRoute(questionsMock);
    render(DeleteQuestionsPage, TEST_DATA);

    expect(screen.getByText("Loading questions...")).toBeInTheDocument();
  });

  it("does not show the selection bar when nothing is selected", async () => {
    mockRoute(questionsMock);
    render(DeleteQuestionsPage, TEST_DATA);

    await waitFor(() => {
      expect(screen.getByText("Response ID")).toBeInTheDocument();
    });

    expect(screen.queryByText(/selected/)).not.toBeInTheDocument();
  });

  it("shows the selection bar when a question is checked", async () => {
    mockRoute(questionsMock);
    render(DeleteQuestionsPage, TEST_DATA);

    await waitFor(() => {
      expect(screen.getByText("Response ID")).toBeInTheDocument();
    });

    await fireEvent.click(screen.getAllByRole("checkbox")[0]);

    expect(screen.getByText("1 selected")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Delete selected questions" }),
    ).toBeInTheDocument();
  });

  it("clears the selection when Clear selection is clicked", async () => {
    mockRoute(questionsMock);
    render(DeleteQuestionsPage, TEST_DATA);

    await waitFor(() => {
      expect(screen.getByText("Response ID")).toBeInTheDocument();
    });

    await fireEvent.click(screen.getAllByRole("checkbox")[0]);
    await fireEvent.click(screen.getByText("Clear selection"));

    expect(screen.queryByText(/selected/)).not.toBeInTheDocument();
  });

  it("opens the confirmation modal when Delete selected questions is clicked", async () => {
    mockRoute(questionsMock);
    render(DeleteQuestionsPage, TEST_DATA);

    await waitFor(() => {
      expect(screen.getByText("Response ID")).toBeInTheDocument();
    });

    await fireEvent.click(screen.getAllByRole("checkbox")[0]);
    await fireEvent.click(
      screen.getByRole("button", { name: "Delete selected questions" }),
    );

    await waitFor(() => {
      expect(
        screen.getByText(
          "Deleting removes the questions and their answers from Consult. This cannot be undone.",
        ),
      ).toBeInTheDocument();
    });
    expect(screen.getAllByText("Response ID").length).toBeGreaterThanOrEqual(2);
  });

  it("shows/hides answers when the toggle is clicked", async () => {
    mockRoute(questionsMock);
    render(DeleteQuestionsPage, TEST_DATA);

    await waitFor(() => {
      expect(screen.getByText("Response ID")).toBeInTheDocument();
    });

    expect(screen.queryByText("R_1Fz8kQp2LmXa9Tb")).not.toBeInTheDocument();
    await fireEvent.click(screen.getAllByText("Show answers")[0]);
    expect(screen.getByText("R_1Fz8kQp2LmXa9Tb")).toBeInTheDocument();
    await fireEvent.click(screen.getByText("Hide answers"));
    expect(screen.queryByText("R_1Fz8kQp2LmXa9Tb")).not.toBeInTheDocument();
  });

  it("deletes selected questions on confirm and shows success message", async () => {
    mockRoute(questionsMock);
    mockRoute(deleteMock(QUESTIONS[0].id));
    mockRoute(questionsMock);
    render(DeleteQuestionsPage, TEST_DATA);

    await waitFor(() => {
      expect(screen.getByText("Response ID")).toBeInTheDocument();
    });

    await fireEvent.click(screen.getAllByRole("checkbox")[0]);
    await fireEvent.click(
      screen.getByRole("button", { name: "Delete selected questions" }),
    );
    await waitFor(() => {
      expect(screen.getByText(/Deleting removes/)).toBeInTheDocument();
    });
    await fireEvent.click(
      screen.getByRole("button", { name: "Delete questions" }),
    );

    await waitFor(() => {
      expect(
        screen.getByText("1 question has been deleted."),
      ).toBeInTheDocument();
    });
  });

  it("matches snapshot", async () => {
    mockRoute(questionsMock);
    const { container } = render(DeleteQuestionsPage, TEST_DATA);
    expect(container).toMatchSnapshot();
  });
});
