import { describe, expect, it, vi } from "vitest";
import { fireEvent, getByRole, render, screen, waitFor } from "@testing-library/svelte";
import userEvent from "@testing-library/user-event";

import { createFetchMock } from "../../../global/utils";
import { getApiConsultationUrl, getApiQuestionsUrl } from "../../../global/routes";

import ThemeSignOffArchive from "./ThemeSignOffArchive.svelte";
import testData from "./testData";

vi.mock("svelte/transition");

describe("ThemeSignOffArchive", () => {
  it("should render questions but not sign off stage", async () => {
    const { fetch: questionsFetch } = createFetchMock([{
      matcher: getApiQuestionsUrl("test-consultation"),
      response: testData
    }]);

    const { getByText } = render(ThemeSignOffArchive, {
      consultationId: "test-consultation",
      questionsFetch: questionsFetch,
    });

    expect(getByText("Theme Sign Off"));
    expect(screen.queryByText("All Questions Signed Off")).toBeFalsy();

    await waitFor(() => {
      testData.results.forEach(question => {
        expect(screen.getByText(`Q${question.number}: ${question.question_text}`)).toBeTruthy();
      })
    });
  });

  it("should display no question if search does not match", async () => {
    const { fetch: questionsFetch } = createFetchMock([{
      matcher: getApiQuestionsUrl("test-consultation"),
      response: testData
    }]);

    render(ThemeSignOffArchive, {
      consultationId: "test-consultation",
      questionsFetch: questionsFetch,
    });

    // Confirm all questions are visible initially
    await waitFor(() => {
      testData.results.forEach(question => {
        expect(screen.getByText(`Q${question.number}: ${question.question_text}`)).toBeTruthy();
      })
    });

    // Search for a query
    const input = screen.getByTestId("search-input");
    await fireEvent.input(input!, { target: { value: "a search query that won't match" } });

    // Confirm no questions are visible as nothing matched the query
    await waitFor(() => {
      testData.results.forEach(question => {
        expect(screen.queryByText(`Q${question.number}: ${question.question_text}`)).toBeFalsy();
      })
    });
  });

  it("should display only the question(s) that match", async () => {
    const { fetch: questionsFetch } = createFetchMock([{
      matcher: getApiQuestionsUrl("test-consultation"),
      response: testData
    }]);

    render(ThemeSignOffArchive, {
      consultationId: "test-consultation",
      questionsFetch: questionsFetch,
    });

    // Confirm all questions are visible initially
    await waitFor(() => {
      testData.results.forEach(question => {
        expect(screen.getByText(`Q${question.number}: ${question.question_text}`)).toBeTruthy();
      })
    });

    // Search for a query
    const queryToSearch = testData.results[0].question_text.slice(0, 20);
    const input = screen.getByTestId("search-input");
    await fireEvent.input(input!, { target: { value: queryToSearch }});

    // Confirm only matching questions are visible
    await waitFor(() => {    
      testData.results.forEach(question => {
        if (question.question_text.includes(queryToSearch)) {
          expect(screen.queryByTestId(question.id)).toBeTruthy();
        } else {
          expect(screen.queryByTestId(question.id)).toBeFalsy();
        }
      })
    });
  });

  it("should display sign off stage if all questions are confirmed", async () => {
    const { fetch: questionsFetch } = createFetchMock([{
      matcher: getApiQuestionsUrl("test-consultation"),
      response: {...testData, results: testData.results.map(question => ({
        ...question,
        theme_status: "confirmed"
      }))},
    }]);
    const { fetch: consultationFetch } = createFetchMock([{
      matcher: getApiQuestionsUrl("test-consultation"),
      response: { stage: "theme_sign_off" },
    }]);

    render(ThemeSignOffArchive, {
      consultationId: "test-consultation",
      questionsFetch: questionsFetch,
      consultationFetch: consultationFetch,
    });

    // Confirm all questions are visible initially
    await waitFor(() => {
      screen.debug()
      expect(screen.getByText("All Questions Signed Off")).toBeTruthy();
    });
  });

  it("should update theme stage when user clicks on confirm", async () => {
    const updateConsultationMock = vi.fn();

    const { fetch: questionsFetch } = createFetchMock([{
      matcher: getApiQuestionsUrl("test-consultation"),
      response: {...testData, results: testData.results.map(question => ({
        ...question,
        theme_status: "confirmed"
      }))},
    }]);

    const { fetch: consultationFetch } = createFetchMock([{
      matcher: getApiConsultationUrl("test-consultation"),
      response: { stage: "theme_sign_off" },
    }]);

    const { fetch: consultationUpdateFetch } = createFetchMock(
      [{
        matcher: getApiConsultationUrl("test-consultation"),
        response: { stage: "theme_sign_off" },
      }],
      ({ options }) => updateConsultationMock(JSON.parse(options.body)),
    );

    render(ThemeSignOffArchive, {
      consultationId: "test-consultation",
      questionsFetch: questionsFetch,
      consultationFetch: consultationFetch,
      consultationUpdateFetch: consultationUpdateFetch,
    });

    let button;
    const user = userEvent.setup();

    // Click on confirm theme sign off button
    await waitFor(() => {
      button = screen.getByText("Confirm and Proceed to Mapping");
    });
    await user.click(button!);

    // Click on confirm button inside confirmation modal
    await waitFor(() => {
      button = screen.getByText("Yes, Start AI Mapping");
    })
    await user.click(button!);

    // Confirm consultation update request has been sent
    await waitFor(() => {
      expect(updateConsultationMock).toHaveBeenCalledWith(
        { stage: "theme_mapping" },
      );
    })
  });
});
