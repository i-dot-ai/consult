import { describe, expect, it } from "vitest";
import { render } from "@testing-library/svelte";

import NotFoundMessage from "./NotFoundMessage.svelte";

describe("Section", () => {
  it("should render title and body", () => {
    const TEST_TITLE = "Test title";
    const TEST_BODY = "Test body";

    const { getByText } = render(NotFoundMessage, {
      title: TEST_TITLE,
      body: TEST_BODY,
    });

    expect(getByText(TEST_TITLE));
    expect(getByText(TEST_BODY));
  });
});
