import { afterEach, beforeEach, describe, expect, it, test, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { render, cleanup, screen } from "@testing-library/svelte";

import { createRawSnippet } from "svelte";

import RespondentTopbar from "./RespondentTopbar.svelte";
import RespondentTopbarStory from "./RespondentTopbarStory.svelte";

let testData: {
  title: string;
  backText: string;
};

describe("RespondentTopbar", () => {
  beforeEach(() => {
    testData = {
      title: "test-title",
      backText: "Back to Analysis",
    };
  });

  afterEach(() => cleanup());

  it("should render data and links", () => {
    const { getByText, container } = render(RespondentTopbar, {
      ...testData,
    });

    expect(getByText(testData.title));
    expect(getByText(testData.backText));
  });

  it("should render child", () => {
    const { getByText, container } = render(RespondentTopbar, {
      ...testData,
      children: createRawSnippet(() => ({
        render: () => `<p>Child content</p>`,
      })),
    });

    expect(getByText(`Child content`));
  });

  it("should call on back click callback", async () => {
    const onClickBackMock = vi.fn();
    const user = userEvent.setup();

    const { getByRole } = render(RespondentTopbar, {
      ...testData,
      onClickBack: onClickBackMock,
      children: createRawSnippet(() => ({
        render: () => `<p>Child content</p>`,
      })),
    });

    const button = getByRole("button");
    await user.click(button);

    expect(onClickBackMock).toHaveBeenCalledOnce();
  });

  it("should render story", () => {
    render(RespondentTopbarStory);
  });
});
