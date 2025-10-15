import { afterEach, describe, expect, it } from "vitest";
import { render, cleanup } from "@testing-library/svelte";

import AnswersList, { type Props } from "./AnswersList.svelte";

describe("AnswersList", () => {
  afterEach(() => cleanup());

  it("should render", async () => {
    const DATA: Props = {
      title: "Test Title",
      answers: ["Answer 1", "Answer 2"],
    };

    const { container, getByText, getAllByText, queryByText } = render(AnswersList, {
      ...DATA,
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
});
