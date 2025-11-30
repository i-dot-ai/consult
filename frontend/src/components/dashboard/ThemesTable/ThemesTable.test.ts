import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { render, cleanup, screen } from "@testing-library/svelte";

import ThemesTable from "./ThemesTable.svelte";
import { getPercentage } from "../../../global/utils";
import ThemesTableStory from "./ThemesTableStory.svelte";

let testData;

describe("ThemesTable", () => {
  beforeEach(() => {
    testData = {
      themes: [
        {
          id: "theme-1",
          name: "Theme 1",
          description: "Test theme 1 description",
          count: 10,
        },
        {
          id: "theme-2",
          name: "Theme 2",
          description: "Test theme 2 description",
          count: 20,
        },
      ],
      totalAnswers: 30,
      skeleton: false,
    };
  });

  afterEach(() => cleanup());

  it("should render data", () => {
    const { getByText } = render(ThemesTable, {
      themes: testData.themes,
      totalAnswers: testData.totalAnswers,
      skeleton: testData.skeleton,
    });

    testData.themes.forEach((theme) => {
      expect(getByText(theme.name));
      expect(getByText(theme.description));
      expect(getByText(theme.count));
      const percentage = getPercentage(theme.count, testData.totalAnswers);
      expect(getByText(`${Math.round(percentage)}%`));
    });
  });

  it("should highlight row if highlighted is true", () => {
    const { container } = render(ThemesTable, {
      themes: testData.themes.map((theme, index) => ({
        ...theme,
        highlighted: index % 2 === 1, // alternate between highlighted
      })),
      totalAnswers: testData.totalAnswers,
      skeleton: testData.skeleton,
    });

    expect(container.querySelectorAll(`tr[aria-pressed="true"]`)).toHaveLength(
      1,
    );
  });

  it("should call handle func if a row is clicked", async () => {
    const user = userEvent.setup();
    const handleClickMock = vi.fn();

    render(ThemesTable, {
      themes: testData.themes.map((theme) => ({
        ...theme,
        handleClick: handleClickMock,
      })),
      totalAnswers: testData.totalAnswers,
      skeleton: testData.skeleton,
    });

    const firstClickableRow = screen.getAllByRole("button").at(0);
    await user.click(firstClickableRow);

    expect(handleClickMock).toHaveBeenCalledOnce();
  });

  it("should not render data if skeleton", () => {
    const { queryByText } = render(ThemesTable, {
      themes: testData.themes,
      totalAnswers: testData.totalAnswers,
      skeleton: true,
    });

    testData.themes.forEach((theme) => {
      expect(queryByText(theme.name)).toBeNull();
      expect(queryByText(theme.description)).toBeNull();
      expect(queryByText(theme.count)).toBeNull();
      const percentage = getPercentage(theme.count, testData.totalAnswers);
      expect(queryByText(`${percentage}%`)).toBeNull();
    });
  });

  it("should render special text when percentage is below 1 but not 0", () => {
    const { getAllByText } = render(ThemesTable, {
      themes: testData.themes,
      totalAnswers: 10000,
      skeleton: false,
    });

    expect(getAllByText("<1%")).toBeTruthy();
  });

  it("should render story", () => {
    render(ThemesTableStory);
  });
});
