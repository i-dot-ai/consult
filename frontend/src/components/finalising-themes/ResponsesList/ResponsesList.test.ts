import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";

import ResponsesList from "./ResponsesList.svelte";
import ResponsesListStory from "./ResponsesListStory.svelte";

describe("ResponsesList", () => {
  const testData = {
    title: "Test Title",
    responses: ["Response 1", "Response 2"],
    totalCount: 2,
  };

  it("should render", async () => {
    const { container } = render(ResponsesList, {
      ...testData,
    });

    expect(screen.getByText("Test Title")).toBeInTheDocument();
    expect(screen.getByText("Response 1")).toBeInTheDocument();
    expect(screen.getByText("Response 2")).toBeInTheDocument();

    // Confirm response 1's number
    expect(screen.getByText("1")).toBeInTheDocument();
    // Finds 2, one is total num of responses, other is response 2's number
    expect(screen.getAllByText("2")).toHaveLength(2);

    // Make sure number don't start at 0
    expect(screen.queryByText("0")).toBeNull();

    expect(container).toMatchSnapshot();
  });

  it("should render not found message if no responses", async () => {
    const NOT_FOUND_MESSAGE = "There are no responses";

    render(ResponsesList, {
      ...testData,
      responses: undefined,
    });

    expect(screen.getByText(NOT_FOUND_MESSAGE)).toBeInTheDocument();
  });

  it("should have a story configured correctly", () => {
    expect(ResponsesListStory).toHaveProperty("name", "ResponsesList");
    expect(ResponsesListStory).toHaveProperty("component", ResponsesList);
    expect(ResponsesListStory).toHaveProperty("props");

    const propsDefined = ResponsesListStory.props.map((prop) => prop.name);
    expect(propsDefined).toEqual(["variant", "title", "responses", "loading"]);
  });
});
