import { afterEach, describe, expect, it } from "vitest";
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
    multiChoiceResponseCount: 30,
  };

  afterEach(() => {
    multiAnswerFilters.reset();
  });

  it("should render data", () => {
    const { container } = render(MultiChoice, {
      data: testData.data,
      multiChoiceResponseCount: testData.multiChoiceResponseCount,
    });

    expect(screen.getByText("30 responses")).toBeInTheDocument();

    testData.data.forEach((item) => {
      expect(screen.getByText(item.text)).toBeInTheDocument();
      expect(screen.getAllByText(item.response_count).length).toBe(2);
      expect(
        screen.getByText(
          `${getPercentage(item.response_count, testData.multiChoiceResponseCount)}%`,
        ),
      ).toBeInTheDocument();
    });

    expect(container).toMatchSnapshot();
  });

  it("should show labels but hide counts when countsLoading is true", () => {
    render(MultiChoice, {
      data: testData.data,
      multiChoiceResponseCount: testData.multiChoiceResponseCount,
      countsLoading: true,
    });

    expect(screen.getByText("Multiple Choice Answers")).toBeInTheDocument();
    testData.data.forEach((item) => {
      expect(screen.getByText(item.text)).toBeInTheDocument();
      expect(screen.queryByText(item.response_count)).not.toBeInTheDocument();
    });
    expect(screen.queryByText("30 responses")).not.toBeInTheDocument();
  });

  it("should toggle multi answer filters when items clicked", async () => {
    const user = userEvent.setup();

    render(MultiChoice, {
      data: testData.data,
      multiChoiceResponseCount: testData.multiChoiceResponseCount,
    });

    // No filters applied yet
    expect(multiAnswerFilters.filters).toStrictEqual([]);

    const buttons = screen.getAllByRole("button");

    // First filter applied
    await user.click(buttons.at(0) as HTMLButtonElement);
    expect(multiAnswerFilters.filters).toStrictEqual([testData.data[0].id]);

    // Second filter applied
    await user.click(buttons.at(1) as HTMLButtonElement);
    expect(multiAnswerFilters.filters).toStrictEqual([
      testData.data[0].id,
      testData.data[1].id,
    ]);

    // First filter removed by clicking on it again
    await user.click(buttons.at(0) as HTMLButtonElement);
    expect(multiAnswerFilters.filters).toStrictEqual([testData.data[1].id]);
  });
});
