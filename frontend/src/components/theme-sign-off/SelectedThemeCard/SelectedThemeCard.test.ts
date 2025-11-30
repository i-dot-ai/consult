import { describe, expect, it } from "vitest";
import { render } from "@testing-library/svelte";

import SelectedThemeCard from "./SelectedThemeCard.svelte";

describe("SelectedThemeCard", () => {
  const testData = {
    theme: {
      id: "theme-id",
      name: "Theme Name",
      description: "This is the theme description",
    },
    answers: ["Answer 1", "Answer 2"],
    removeTheme: () => {},
    updateTheme: () => {},
  };

  it("should render", async () => {
    const { container, getByText, queryByText } = render(
      SelectedThemeCard,
      testData,
    );

    expect(getByText(testData.theme.name));
    expect(getByText(testData.theme.description));

    // Answers hidden initially
    testData.answers?.forEach((answer) => {
      expect(queryByText(answer)).toBeNull();
    });

    expect(container).toMatchSnapshot();
  });
});
