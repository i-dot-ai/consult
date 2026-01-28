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
    collapsedThemes: [] as string[], // Empty = all expanded
    toggleTheme: () => {},
    handleSelect: () => {},
    themesBeingSelected: [] as string[],
  };

  it("should render", async () => {
    const { container } = render(CandidateThemeCard, {
      props: testData,
    });

    expect(screen.getByText(testData.theme.name)).toBeInTheDocument();
    expect(screen.getByText(testData.theme.description)).toBeInTheDocument();

    expect(container).toMatchSnapshot();
  });

  it("should render recursively", async () => {
    const CHILD_THEME = {
      id: "child-theme",
      name: "Child Theme",
      description: "This is a child theme",
    };
    render(CandidateThemeCard, {
      props: {
        ...testData,
        collapsedThemes: [], // Empty = all expanded
        theme: {
          ...testData.theme,
          children: [CHILD_THEME],
        },
      },
    });

    expect(screen.getByText(CHILD_THEME.name)).toBeInTheDocument();
    expect(screen.getByText(CHILD_THEME.description)).toBeInTheDocument();
  });

  it("should not render child if theme is collapsed", async () => {
    const CHILD_THEME = {
      id: "child-theme",
      name: "Child Theme",
      description: "This is a child theme",
    };
    render(CandidateThemeCard, {
      props: {
        ...testData,
        collapsedThemes: ["test-theme"], // Parent theme is collapsed
        theme: {
          ...testData.theme,
          children: [CHILD_THEME],
        },
      },
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
      "consultationId",
      "questionId",
      "theme",
      "collapsedThemes",
      "level",
      "leftPadding",
      "handleSelect",
    ]);
  });
});
