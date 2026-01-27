import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";

import CandidateThemeCard from "./CandidateThemeCard.svelte";
import CandidateThemeCardStory from "./CandidateThemeCard.story.svelte";

describe("CandidateThemeCard", () => {
  const testData = {
    consultationId: "test-consultation",
    questionId: "test-question",
    theme: {
      id: "test-theme",
      name: "Test Theme",
      description: "This is a test theme",
    },
    expandedThemes: [],
    setExpandedThemes: () => {},
    handleSelect: () => {},
    themesBeingSelected: [],
  };
  const answers = ["Answer 1", "Answer 2"];

  it("should render", async () => {
    const { container } = render(CandidateThemeCard, testData);

    expect(screen.getByText(testData.theme.name)).toBeInTheDocument();
    expect(screen.getByText(testData.theme.description)).toBeInTheDocument();

    // Answers hidden initially
    answers.forEach((answer) => {
      expect(screen.queryByText(answer)).toBeNull();
    });

    expect(container).toMatchSnapshot();
  });

  it("should render recursively", async () => {
    const CHILD_THEME = {
      id: "child-theme",
      name: "Child Theme",
      description: "This is a child theme",
    };
    render(CandidateThemeCard, {
      ...testData,
      theme: {
        ...testData.theme,
        children: [CHILD_THEME],
      },
      expandedThemes: [testData.theme.id, CHILD_THEME.id],
    });

    expect(screen.getByText(CHILD_THEME.name)).toBeInTheDocument();
    expect(screen.getByText(CHILD_THEME.description)).toBeInTheDocument();
  });

  it("should not render child if theme is not expanded", async () => {
    const CHILD_THEME = {
      id: "child-theme",
      name: "Child Theme",
      description: "This is a child theme",
    };
    render(CandidateThemeCard, {
      ...testData,
      theme: {
        ...testData.theme,
        children: [CHILD_THEME],
      },
      expandedThemes: [],
    });

    expect(screen.queryByText(CHILD_THEME.name)).toBeNull();
    expect(screen.queryByText(CHILD_THEME.description)).toBeNull();
  });

  it("should have a story configured correctly", () => {
    expect(CandidateThemeCardStory).toHaveProperty(
      "name",
      "CandidateThemeCard",
    );
    expect(CandidateThemeCardStory).toHaveProperty(
      "component",
      CandidateThemeCard,
    );
    expect(CandidateThemeCardStory).toHaveProperty("props");

    const propsDefined = CandidateThemeCardStory.props.map((prop) => prop.name);
    expect(propsDefined).toEqual([
      "theme",
      "level",
      "leftPadding",
      "handleSelect",
      "answersMock",
    ]);
  });
});
