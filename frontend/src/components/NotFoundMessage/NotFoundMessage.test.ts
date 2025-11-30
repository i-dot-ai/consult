import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";

import NotFoundMessage from "./NotFoundMessage.svelte";

describe("Section", () => {
  it("should render title and body", () => {
    const TEST_TITLE = "Test title";
    const TEST_BODY = "Test body";

    render(NotFoundMessage, {
      title: TEST_TITLE,
      body: TEST_BODY,
    });

    expect(screen.getByText(TEST_TITLE)).toBeInTheDocument();
    expect(screen.getByText(TEST_BODY)).toBeInTheDocument();
  });
});
