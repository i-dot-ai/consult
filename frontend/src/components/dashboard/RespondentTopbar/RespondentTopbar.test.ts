import { describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { render } from "@testing-library/svelte";

import { createRawSnippet } from "svelte";

import RespondentTopbar from "./RespondentTopbar.svelte";

describe("RespondentTopbar", () => {
  const testData = {
    title: "test-title",
    backText: "Back to Analysis",
  };

  it("should render data and links", () => {
    const { getByText } = render(RespondentTopbar, {
      ...testData,
    });

    expect(getByText(testData.title)).toBeInTheDocument();
    expect(getByText(testData.backText)).toBeInTheDocument();
  });

  it("should render child", () => {
    const { getByText } = render(RespondentTopbar, {
      ...testData,
      children: createRawSnippet(() => ({
        render: () => `<p>Child content</p>`,
      })),
    });

    expect(getByText(`Child content`)).toBeInTheDocument();
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
});
