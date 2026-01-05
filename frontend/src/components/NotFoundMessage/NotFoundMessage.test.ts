import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";

import NotFoundMessage from "./NotFoundMessage.svelte";

describe("Section", () => {
  const testData = {
    title: "Test title",
    body: "Test body",
  };

  it("should render title", () => {
    render(NotFoundMessage, testData);

    expect(screen.getByText(testData.title)).toBeInTheDocument();
  });

  it("should render body", () => {
    render(NotFoundMessage, testData);

    expect(screen.getByText(testData.body)).toBeInTheDocument();
  });

  it("should match snapshot", () => {
    const { container } = render(NotFoundMessage, testData);

    expect(container).toMatchSnapshot();
  });
});
