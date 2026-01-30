import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/svelte";

import RepresentativeResponses from "./RepresentativeResponses.svelte";
import RepresentativeResponsesStory from "./RepresentativeResponses.story.svelte";
import { queryClient } from "../../../../global/queryClient";

const mockFetch = vi.fn();

describe("RepresentativeResponses", () => {
  const testData = {
    consultationId: "test-consultation",
    questionId: "test-question",
    themeName: "Test Theme",
    themeDescription: "Test theme description",
    themeId: "test-theme-id",
    variant: "selected" as const,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    queryClient.clear();
    global.fetch = mockFetch;
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should render with loading state", async () => {
    // Don't resolve fetch to keep loading state
    mockFetch.mockReturnValue(new Promise(() => {}));

    const { container } = render(RepresentativeResponses, {
      props: testData,
    });

    expect(screen.getByText("Representative Responses")).toBeInTheDocument();
    expect(container).toMatchSnapshot();
  });

  it("should render with responses when loaded", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          all_respondents: [
            { free_text_answer_text: "First response text" },
            { free_text_answer_text: "Second response text" },
          ],
        }),
    });

    render(RepresentativeResponses, {
      props: testData,
    });

    await waitFor(() => {
      expect(screen.getByText("First response text")).toBeInTheDocument();
    });

    expect(screen.getByText("Second response text")).toBeInTheDocument();
  });

  it("should render empty state when no responses", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          all_respondents: [],
        }),
    });

    render(RepresentativeResponses, {
      props: testData,
    });

    await waitFor(() => {
      expect(screen.getByText("0")).toBeInTheDocument();
    });

    expect(screen.getByText("There are no answers")).toBeInTheDocument();
  });

  it("should have a story configured correctly", () => {
    expect(RepresentativeResponsesStory).toHaveProperty(
      "name",
      "RepresentativeResponses",
    );
    expect(RepresentativeResponsesStory).toHaveProperty(
      "component",
      RepresentativeResponses,
    );
    expect(RepresentativeResponsesStory).toHaveProperty("props");

    const propsDefined = RepresentativeResponsesStory.props.map(
      (prop) => prop.name,
    );
    expect(propsDefined).toEqual([
      "consultationId",
      "questionId",
      "themeName",
      "themeDescription",
      "themeId",
      "variant",
    ]);
  });
});
