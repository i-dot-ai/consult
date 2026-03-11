import { render, fireEvent, screen } from "@testing-library/svelte";
import { describe, it, expect, vi } from "vitest";

import FileInput from "./FileInput.svelte";
import { TEST_DATA } from "./testData";
import userEvent from "@testing-library/user-event";

describe("FileInput Component", () => {
  const testData = {...TEST_DATA, onConfirm: vi.fn()};

  const FILE_ONE = new File(["test"], "test1.csv", { type: "text/csv"});
  const FILE_TWO = new File(["test"], "test2.csv", { type: "text/csv"});

  it("calls onConfirm with selected files", async () => {
    render(FileInput, testData);
    
    const inputEl = screen.getByTestId("file-input");
    

    const user = userEvent.setup();
    await fireEvent.change(inputEl, {
      target: {
        files: [FILE_ONE],
      }
    });

    await user.click(screen.getByRole("button", { name: "Confirm" }));

    expect(testData.onConfirm).toHaveBeenCalledWith([FILE_ONE]);
  });

  it("calls onConfirm with multiple selected files", async () => {
    render(FileInput, testData);
    
    const inputEl = screen.getByTestId("file-input");
    

    const user = userEvent.setup();
    await fireEvent.change(inputEl, {
      target: {
        files: [FILE_ONE, FILE_TWO],
      }
    });

    await user.click(screen.getByRole("button", { name: "Confirm" }));

    expect(testData.onConfirm).toHaveBeenCalledWith([FILE_ONE, FILE_TWO]);
  });

  it("refuses files if file maxSize is exceeded", async () => {
    render(FileInput, {...testData, maxSize: 0});

    const inputEl = screen.getByTestId("file-input");

    await fireEvent.change(inputEl, {
      target: {
        files: [FILE_ONE, FILE_TWO],
      }
    });

    expect(screen.queryByRole("button", { name: "Confirm" })).not.toBeInTheDocument();
    expect(screen.getByText("File size limit exceeded")).toBeInTheDocument();
  });

  it("renders accept string", () => {
    const ACCEPT =  "text/csv";
    render(FileInput, {...testData, accept: ACCEPT});

    const inputEl = screen.getByTestId("file-input");

    expect(inputEl).toHaveAttribute("accept", ACCEPT);
  });

  it("renders id", () => {
    render(FileInput, testData);

    const inputEl = screen.getByTestId("file-input");

    expect(inputEl).toHaveAttribute("id", testData.id);
  });

  it("renders title", () => {
    render(FileInput, testData);

    expect(screen.getByText(testData.title)).toBeInTheDocument();
  });

  it("renders subtitle", () => {
    render(FileInput, testData);

    expect(screen.getByText(testData.subtitle)).toBeInTheDocument();
  });

  it("should match snapshot", () => {
    const { container } = render(FileInput);
    expect(container).toMatchSnapshot();
  });
});
