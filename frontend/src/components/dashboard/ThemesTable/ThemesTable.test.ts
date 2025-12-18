import { describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { render, screen } from "@testing-library/svelte";

import ThemesTable from "./ThemesTable.svelte";
import { getPercentage } from "../../../global/utils";

describe("ThemesTable", () => {
  const testData = {
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

  it("should render data", () => {
    render(ThemesTable, {
      themes: testData.themes,
      totalAnswers: testData.totalAnswers,
      skeleton: testData.skeleton,
    });

    testData.themes.forEach((theme) => {
      expect(screen.getByText(theme.name)).toBeInTheDocument();
      expect(screen.getByText(theme.description)).toBeInTheDocument();
      expect(screen.getByText(theme.count)).toBeInTheDocument();
      const percentage = getPercentage(theme.count, testData.totalAnswers);
      expect(
        screen.getByText(`${Math.round(percentage)}%`),
      ).toBeInTheDocument();
    });
  });

  it("should highlight row if highlighted is true", () => {
    render(ThemesTable, {
      themes: testData.themes.map((theme, index) => ({
        ...theme,
        highlighted: index % 2 === 1, // alternate between highlighted
      })),
      totalAnswers: testData.totalAnswers,
      skeleton: testData.skeleton,
    });

    expect(screen.getAllByRole("button", { pressed: true })).toHaveLength(1);
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

    const firstClickableRow = screen
      .getAllByRole("button")
      .at(0) as HTMLButtonElement;
    await user.click(firstClickableRow);

    expect(handleClickMock).toHaveBeenCalledOnce();
  });

  it("should not render data if skeleton", () => {
    render(ThemesTable, {
      themes: testData.themes,
      totalAnswers: testData.totalAnswers,
      skeleton: true,
    });

    testData.themes.forEach((theme) => {
      expect(screen.queryByText(theme.name)).toBeNull();
      expect(screen.queryByText(theme.description)).toBeNull();
      expect(screen.queryByText(theme.count)).toBeNull();
      const percentage = getPercentage(theme.count, testData.totalAnswers);
      expect(screen.queryByText(`${percentage}%`)).toBeNull();
    });
  });

  it("should render special text when percentage is below 1 but not 0", () => {
    render(ThemesTable, {
      themes: testData.themes,
      totalAnswers: 10000,
      skeleton: false,
    });

    expect(screen.getAllByText("<1%")).toBeTruthy();
  });
});
