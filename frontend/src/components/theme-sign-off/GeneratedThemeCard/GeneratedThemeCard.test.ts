import { describe, expect, it, vi } from "vitest";
import { render } from "@testing-library/svelte";

import GeneratedThemeCard from "./GeneratedThemeCard.svelte";

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
  };
  const answers = ["Answer 1", "Answer 2"];

  it("should render", async () => {
    vi.mock("svelte/transition");

    const { container, getByText, queryByText } = render(
      GeneratedThemeCard,
      testData,
    );

    expect(getByText(testData.theme.name));
    expect(getByText(testData.theme.description));

    // Answers hidden initially
    answers.forEach((answer) => {
      expect(queryByText(answer)).toBeNull();
    });

    expect(container).toMatchSnapshot();
  });

  it("should render recursively", async () => {
    const CHILD_THEME = {
      id: "child-theme",
      name: "Child Theme",
      description: "This is a child theme",
    };
    const { getByText } = render(GeneratedThemeCard, {
      ...testData,
      theme: {
        ...testData.theme,
        children: [CHILD_THEME],
      },
      expandedThemes: [testData.theme.id, CHILD_THEME.id],
    });

    expect(getByText(CHILD_THEME.name));
    expect(getByText(CHILD_THEME.description));
  });

  it("should not render child if theme is not expanded", async () => {
    const CHILD_THEME = {
      id: "child-theme",
      name: "Child Theme",
      description: "This is a child theme",
    };
    const { queryByText } = render(GeneratedThemeCard, {
      ...testData,
      theme: {
        ...testData.theme,
        children: [CHILD_THEME],
      },
      expandedThemes: [],
    });

    expect(queryByText(CHILD_THEME.name)).toBeNull();
    expect(queryByText(CHILD_THEME.description)).toBeNull();
  });
});
