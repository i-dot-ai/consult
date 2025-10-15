import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { render, cleanup } from "@testing-library/svelte";

import AnswersList, { type Props } from "./AnswersList.svelte";

let testData: Props;

describe("AnswersList", () => {
  beforeEach(() => {
    testData = {
      title: "Test Title",
      answers: ["Answer 1", "Answer 2"],
    };
  })

  afterEach(() => cleanup());

  it("should render", async () => {
    const { container, getByText, getAllByText, queryByText } = render(AnswersList, {
      ...testData,
    });

    expect(getByText("Test Title"));
    expect(getByText("Answer 1"));
    expect(getByText("Answer 2"));

    // Confirm answeer 1's number
    expect(getByText("1"));
    // Finds 2, one is total num of answers, other is answer 2's number
    expect(getAllByText("2")).toHaveLength(2);

    // Make sure number don't start at 0
    expect(queryByText("0")).toBeNull();

    expect(container).toMatchSnapshot();
  });

  it("should render not found message if no answers", async () => {
    const NOT_FOUND_MESSAGE = "There are no answers";

    const { getByText } = render(AnswersList, {
      ...testData,
      answers: undefined,
    });

    expect(getByText(NOT_FOUND_MESSAGE));
  })
});
