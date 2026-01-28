import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/svelte";

import SelectedThemeCard from "./SelectedThemeCard.svelte";
import SelectedThemeCardStory from "./SelectedThemeCardStory.svelte";

describe("SelectedThemeCard", () => {
  const testData = {
    consultationId: "test-consultation",
    questionId: "test-question",
    showError: vi.fn(),
    theme: {
      id: "theme-id",
      name: "Theme Name",
      description: "This is the theme description",
      version: 1,
      modified_at: new Date().toISOString(),
      last_modified_by: "testuser",
    },
  };

  it("should render", async () => {
    const { container } = render(SelectedThemeCard, {
      props: testData,
    });

    expect(screen.getByText(testData.theme.name)).toBeInTheDocument();
    expect(screen.getByText(testData.theme.description)).toBeInTheDocument();

    expect(container).toMatchSnapshot();
  });

  it("should have a story configured correctly", () => {
    expect(SelectedThemeCardStory).toHaveProperty("name", "SelectedThemeCard");
    expect(SelectedThemeCardStory).toHaveProperty(
      "component",
      SelectedThemeCard,
    );
    expect(SelectedThemeCardStory).toHaveProperty("props");

    const propsDefined = SelectedThemeCardStory.props.map((prop) => prop.name);
    expect(propsDefined).toEqual([
      "consultationId",
      "questionId",
      "showError",
      "theme",
    ]);
  });
});
