import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/svelte";

import FileVerified from "./FileVerified.svelte";
import userEvent from "@testing-library/user-event";

describe("FileVerified", () => {
  const testData = {
    numQuestions: 25,
  };

  it("renders title", () => {
    render(FileVerified, testData);

    expect(screen.getByText("File structure valid")).toBeInTheDocument();
  });

  it.each([0, 10, 100, 1000])("renders number of questions", (numQuestions) => {
    render(FileVerified, { ...testData, numQuestions });

    expect(screen.getByText(numQuestions.toString())).toBeInTheDocument();
  });

  it("renders 0 if number of questions is negative", () => {
    render(FileVerified, { ...testData, numQuestions: -1 });

    expect(screen.getByText("0")).toBeInTheDocument();
  });

  it("should match snapshot", () => {
    const { container } = render(FileVerified, testData);
    expect(container).toMatchSnapshot();
  });
});
