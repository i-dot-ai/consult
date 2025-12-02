import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";

import TagTest from "./TagTest.svelte";

describe("Tag", () => {
  it("should render", async () => {
    const TAG_CONTENT = "Tag Content";

    render(TagTest, {
      content: TAG_CONTENT,
    });

    expect(screen.getByText(TAG_CONTENT)).toBeInTheDocument();
  });
});
