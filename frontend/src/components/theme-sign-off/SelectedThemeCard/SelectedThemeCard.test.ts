import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";

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
    const { container } = render(SelectedThemeCard, testData);

    expect(screen.getByText(testData.theme.name)).toBeInTheDocument();
    expect(screen.getByText(testData.theme.description)).toBeInTheDocument();

    // Answers hidden initially
    testData.answers?.forEach((answer) => {
      expect(screen.queryByText(answer)).toBeNull();
    });

    expect(container).toMatchSnapshot();
  });
});
