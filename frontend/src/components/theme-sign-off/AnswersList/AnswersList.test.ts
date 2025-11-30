import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";

import AnswersList from "./AnswersList.svelte";

describe("AnswersList", () => {
  const testData = {
    title: "Test Title",
    answers: ["Answer 1", "Answer 2"],
  };

  it("should render", async () => {
    const { container } = render(AnswersList, {
      ...testData,
    });

    expect(screen.getByText("Test Title")).toBeInTheDocument();
    expect(screen.getByText("Answer 1")).toBeInTheDocument();
    expect(screen.getByText("Answer 2")).toBeInTheDocument();

    // Confirm answeer 1's number
    expect(screen.getByText("1")).toBeInTheDocument();
    // Finds 2, one is total num of answers, other is answer 2's number
    expect(screen.getAllByText("2")).toHaveLength(2);

    // Make sure number don't start at 0
    expect(screen.queryByText("0")).toBeNull();

    expect(container).toMatchSnapshot();
  });

  it("should render not found message if no answers", async () => {
    const NOT_FOUND_MESSAGE = "There are no answers";

    render(AnswersList, {
      ...testData,
      answers: undefined,
    });

    expect(screen.getByText(NOT_FOUND_MESSAGE)).toBeInTheDocument();
  });
});
