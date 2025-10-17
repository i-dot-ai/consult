import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { render, cleanup } from "@testing-library/svelte";

import SelectedThemeCard, { type Props } from "./SelectedThemeCard.svelte";

let testData: Props;

describe("SelectedThemeCard", () => {
  beforeEach(() => {
    testData = {
      theme: {
        id: "theme-id",
        name: "Theme Name",
        description: "This is the theme description",
      },
      answers: ["Answer 1", "Answer 2"],
      removeTheme: () => {},
      updateTheme: () => {},
    };
  });

  afterEach(() => cleanup());

  it("should render", async () => {
    const { container, getByText, queryByText } = render(SelectedThemeCard, {
      ...testData,
    });

    expect(getByText(testData.theme.name));
    expect(getByText(testData.theme.description));

    // Answers hidden initially
    testData.answers?.forEach((answer) => {
      expect(queryByText(answer)).toBeNull();
    });

    expect(container).toMatchSnapshot();
  });
});
