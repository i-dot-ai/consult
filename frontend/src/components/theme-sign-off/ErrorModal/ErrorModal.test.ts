import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/svelte";

import ErrorModal, { type ErrorModalProps } from "./ErrorModal.svelte";
import userEvent from "@testing-library/user-event";

describe("ErrorModal", () => {
  const testData: ErrorModalProps = {
    type: "unexpected",
    onClose: vi.fn(),
  }

  it("should render message initially", async () => {
    render(ErrorModal);

    expect(screen.getByTestId("content")).toBeInTheDocument();
  });

  it.each(["edit-conflict", "remove-conflict"])("should render modified date and person", (type) => {
    const LAST_MODIFIED_BY = "test-person";
    const LATEST_VERSION = "12345";
    render(ErrorModal, {
      type: type as ErrorModalProps["type"],
      lastModifiedBy: LAST_MODIFIED_BY,
      latestVersion: LATEST_VERSION,
      onClose: testData.onClose,
    })

    expect(screen.getByTestId("content")).toHaveTextContent(LAST_MODIFIED_BY);
  })

  it("should close when close button is clicked", async () => {
    const user = userEvent.setup();
    const onCloseMock = vi.fn();
    render(ErrorModal, {
      ...testData,
      onClose: onCloseMock,
    });

    const button = screen.getByRole("button");
    await user.click(button);

    expect(screen.queryByTestId("content")).not.toBeInTheDocument();
    expect(onCloseMock).toHaveBeenCalledOnce();
  });

  it("should match snapshot", async () => {
    const { container } = render(ErrorModal);

    expect(container).toMatchSnapshot();
  });
});
