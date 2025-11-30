import { describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { render, screen } from "@testing-library/svelte";

import { createRawSnippet } from "svelte";

import RespondentTopbar from "./RespondentTopbar.svelte";

describe("RespondentTopbar", () => {
  const testData = {
    title: "test-title",
    backText: "Back to Analysis",
  };

  it("should render data and links", () => {
    render(RespondentTopbar, {
      ...testData,
    });

    expect(screen.getByText(testData.title)).toBeInTheDocument();
    expect(screen.getByText(testData.backText)).toBeInTheDocument();
  });

  it("should render child", () => {
    render(RespondentTopbar, {
      ...testData,
      children: createRawSnippet(() => ({
        render: () => `<p>Child content</p>`,
      })),
    });

    expect(screen.getByText(`Child content`)).toBeInTheDocument();
  });

  it("should call on back click callback", async () => {
    const onClickBackMock = vi.fn();
    const user = userEvent.setup();

    render(RespondentTopbar, {
      ...testData,
      onClickBack: onClickBackMock,
      children: createRawSnippet(() => ({
        render: () => `<p>Child content</p>`,
      })),
    });

    const button = screen.getByRole("button");
    await user.click(button);

    expect(onClickBackMock).toHaveBeenCalledOnce();
  });
});
