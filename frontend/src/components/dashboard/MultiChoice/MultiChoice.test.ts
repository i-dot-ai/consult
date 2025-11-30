import { afterEach, describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { render, screen } from "@testing-library/svelte";

import { getPercentage } from "../../../global/utils";
import { multiAnswerFilters } from "../../../global/state.svelte";

import MultiChoice from "./MultiChoice.svelte";

describe("MultiChoice", () => {
  const testData = {
    data: [
      {
        id: "id-1",
        text: "Multi Choice Answer 1",
        response_count: 10,
      },
      {
        id: "id-2",
        text: "Multi Choice Answer 2",
        response_count: 20,
      },
    ],
    totalCounts: 30,
  };

  afterEach(() => {
    multiAnswerFilters.reset();
  });

  it("should render data", () => {
    vi.mock("svelte/transition");

    const { container, getByText, getAllByText } = render(MultiChoice, {
      data: testData.data,
    });

    testData.data.forEach((item) => {
      expect(getByText(item.text));
      expect(getAllByText(item.response_count).length).toBe(2);
      expect(
        getByText(
          `${getPercentage(item.response_count, testData.totalCounts)}%`,
        ),
      );
    });

    expect(container).toMatchSnapshot();
  });

  it("should toggle multi answer filters when items clicked", async () => {
    const user = userEvent.setup();

    render(MultiChoice, { data: testData.data });

    // No filters applied yet
    expect(multiAnswerFilters.filters).toStrictEqual([]);

    const buttons = screen.getAllByRole("button");

    // First filter applied
    await user.click(buttons.at(0));
    expect(multiAnswerFilters.filters).toStrictEqual([testData.data[0].id]);

    // Second filter applied
    await user.click(buttons.at(1));
    expect(multiAnswerFilters.filters).toStrictEqual([
      testData.data[0].id,
      testData.data[1].id,
    ]);

    // First filter removed by clicking on it again
    await user.click(buttons.at(0));
    expect(multiAnswerFilters.filters).toStrictEqual([testData.data[1].id]);
  });
});
