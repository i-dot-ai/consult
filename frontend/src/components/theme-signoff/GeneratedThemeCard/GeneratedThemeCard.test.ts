import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { render, cleanup } from "@testing-library/svelte";

import GeneratedThemeCard, { type Props } from "./GeneratedThemeCard.svelte";

let testData: Props;

describe("GeneratedThemeCard", () => {
  beforeEach(() => {
    testData = {
      selectedThemes: [],
      theme: {
        id: "test-theme",
        name: "Test Theme",
        description: "This is a test theme",
      },
      answers: ["Answer 1", "Answer 2"],
      handleSelect: () => {},
    };
  })

  afterEach(() => cleanup());

  it("should render", async () => {
    const { container, getByText, getAllByText, queryByText } = render(GeneratedThemeCard, {
      ...testData,
    });

    expect(getByText(testData.theme.name));
    expect(getByText(testData.theme.description));

    // Answers hidden initially
    testData.answers?.forEach(answer => {
      expect(queryByText(answer)).toBeNull();
    })

    expect(container).toMatchSnapshot();
  });

  it("should render recursively", async () => {
    const CHILD_THEME = {
      id: "child-theme",
      name: "Child Theme",
      description: "This is a child theme",
    }
    const { container, getByText, getAllByText, queryByText } = render(GeneratedThemeCard, {
      ...testData,
      theme: {
        ...testData.theme,
        children: [
          CHILD_THEME,
        ]
      }
    });

    expect(getByText(CHILD_THEME.name));
    expect(getByText(CHILD_THEME.description));
  });
});
