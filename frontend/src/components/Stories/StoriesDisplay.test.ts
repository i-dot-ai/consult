import { describe, expect, it } from "vitest";
import { render, screen, waitFor } from "@testing-library/svelte";

import StoriesDisplay from "./StoriesDisplay.svelte";
import stories from "./stories";

const categories = [...new Set(stories.map(story => story.category).filter(category => Boolean(category)))];

describe("StoriesDisplay", () => {
  it.each(categories)(
    "should render categories",
    async (category) => {
      render(StoriesDisplay);

      await waitFor(() => {
        expect(screen.getByRole("heading", { name: category! })).toBeInTheDocument();
      });
    },
  );

  it.each(stories)(
    "should render story titles",
    async (story) => {
      render(StoriesDisplay);

      await waitFor(() => {
        expect(screen.getByRole("link", { name: story.name! })).toBeInTheDocument();
      });
    },
  );

  it("should match snapshot", async () => {
    const { container } = render(StoriesDisplay);

    expect(container).toMatchSnapshot();
  })
});
