import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/svelte";

import { createFetchMock } from "../../../global/utils";
import { getApiQuestionsUrl } from "../../../global/routes";

import ThemeSignOffArchive from "./ThemeSignOffArchive.svelte";
import testData from "./testData";

vi.mock("svelte/transition");

describe("ThemeSignOffArchive", () => {
  it("should render questions", async () => {
    const { fetch: questionsFetch } = createFetchMock([{
      matcher: getApiQuestionsUrl("test-consultation"),
      response: testData
    }]);

    const { getByText } = render(ThemeSignOffArchive, {
      consultationId: "test-consultation",
      mockFetch: questionsFetch,
    });

    expect(getByText("Theme Sign Off"));

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
      mockFetch: questionsFetch,
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
      mockFetch: questionsFetch,
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
});
