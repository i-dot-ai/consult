import { afterEach, describe, expect, it } from "vitest";
import { render, cleanup } from "@testing-library/svelte";

import TagTest from "./TagTest.svelte";

describe("Tag", () => {
  afterEach(() => cleanup());

  it("should render", async () => {
    const TAG_CONTENT = "Tag Content";

    const { getByText } = render(TagTest, {
      content: TAG_CONTENT,
    });

    expect(getByText(TAG_CONTENT));
  });
});
