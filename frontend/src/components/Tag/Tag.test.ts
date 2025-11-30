import { describe, expect, it } from "vitest";
import { render } from "@testing-library/svelte";

import TagTest from "./TagTest.svelte";

describe("Tag", () => {
  it("should render", async () => {
    const TAG_CONTENT = "Tag Content";

    const { getByText } = render(TagTest, {
      content: TAG_CONTENT,
    });

    expect(getByText(TAG_CONTENT)).toBeInTheDocument();
  });
});
