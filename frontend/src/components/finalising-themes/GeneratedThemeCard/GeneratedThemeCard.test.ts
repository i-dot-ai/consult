import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";

import GeneratedThemeCard from "./GeneratedThemeCard.svelte";
import GeneratedThemeCardStory from "./GeneratedThemeCardStory.svelte";

describe("GeneratedThemeCard", () => {
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
    hasNestedThemes: false,
  };
  const responses = ["Answer 1", "Answer 2"];

  it("should render", async () => {
    const { container } = render(GeneratedThemeCard, testData);

    expect(screen.getByText(testData.theme.name)).toBeInTheDocument();
    expect(screen.getByText(testData.theme.description)).toBeInTheDocument();

    // Responses hidden initially
    responses.forEach((response) => {
      expect(screen.queryByText(response)).toBeNull();
    });

    expect(container).toMatchSnapshot();
  });

  it("should render recursively", async () => {
    const CHILD_THEME = {
      id: "child-theme",
      name: "Child Theme",
      description: "This is a child theme",
    };
    render(GeneratedThemeCard, {
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
    render(GeneratedThemeCard, {
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
    expect(GeneratedThemeCardStory).toHaveProperty(
      "name",
      "GeneratedThemeCard",
    );
    expect(GeneratedThemeCardStory).toHaveProperty(
      "component",
      GeneratedThemeCard,
    );
    expect(GeneratedThemeCardStory).toHaveProperty("props");

    const propsDefined = GeneratedThemeCardStory.props.map((prop) => prop.name);
    expect(propsDefined).toEqual([
      "consultationId",
      "questionId",
      "theme",
      "expandedThemes",
      "hasNestedThemes",
      "level",
      "leftPadding",
      "handleSelect",
      "responsesMock",
      "setExpandedThemes",
    ]);
  });

  it("should render level tag only if theme has children", async () => {
    const CHILD_THEME = {
      id: "child-theme",
      name: "Child Theme",
      description: "This is a child theme",
    };
    render(GeneratedThemeCard, {
      ...testData,
      hasNestedThemes: true,
      theme: {
        ...testData.theme,
        children: [CHILD_THEME],
      },
      expandedThemes: [testData.theme.id],
    });

    expect(screen.getByText("Level 1")).toBeInTheDocument();
  });

  it("should not render level tag if theme has no children", async () => {
    render(GeneratedThemeCard, {
      ...testData,
      theme: {
        ...testData.theme,
        children: [],
      },
      expandedThemes: [testData.theme.id],
    });

    expect(screen.queryByText("Level 1")).toBeNull();
  });
});
