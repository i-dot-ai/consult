import { beforeEach, afterEach, describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { render, cleanup, screen, fireEvent, act } from "@testing-library/svelte";

import { createRawSnippet } from "svelte";

import Modal, { type Props } from "./Modal.svelte";

let testData: Props;

describe("Modal", () => {
  beforeEach(() => {
    testData = {
      title: "Test Title",
      confirmText: "Ok",
      children: createRawSnippet(() => ({
        render: () => "<p>Child Element</p>",
      })),
      handleConfirm: () => {},
      setOpen: () => {},
    }
  })
  afterEach(() => cleanup());

  it("does not render contents if closed", async () => {
    const { component, queryByText } = render(Modal, {
      ...testData,
    });

    // store does not update without this
    await act(() => component.setImperativeOpen(false));

    expect(queryByText("Ok")).toBeNull();
  });

  it("should render contents if open", async () => {
    const handleConfirmMock = vi.fn();
    const setOpenMock = vi.fn();

    expect(testData).toBeTruthy()
    const { component, getByText } = render(Modal, {
      ...testData,
      handleConfirm: handleConfirmMock,
      setOpen: setOpenMock,
    });

    // store does not update without this
    await act(() => component.setImperativeOpen(true));

    expect(getByText(testData.title));
    expect(getByText(testData.confirmText));
  });

  it("should call confirm callback when clicked", async () => {
    vi.mock("svelte/transition");

    const handleConfirmMock = vi.fn();
    const setOpenMock = vi.fn();

    expect(testData).toBeTruthy()
    const { component, getByText } = render(Modal, {
      ...testData,
      handleConfirm: handleConfirmMock,
      setOpen: setOpenMock,
    });

    // store does not update without this
    await act(() => component.setImperativeOpen(true));

    expect(getByText("Ok"));
    const confirmButton = screen.getByText("Ok");

    await fireEvent.click(confirmButton);

    expect(setOpenMock).toHaveBeenCalledOnce();
    expect(handleConfirmMock).toHaveBeenCalledOnce();
  });

  it("should not call confirm callback when cancel is clicked", async () => {
    vi.mock("svelte/transition");

    const handleConfirmMock = vi.fn();
    const setOpenMock = vi.fn();

    expect(testData).toBeTruthy()
    const { component, getByText } = render(Modal, {
      ...testData,
      handleConfirm: handleConfirmMock,
      setOpen: setOpenMock,
    });

    // store does not update without this - TODO: Fix meltOpen update
    await act(() => component.setImperativeOpen(true));

    expect(getByText("Ok"));
    const cancelButton = screen.getByText("Cancel");

    await fireEvent.click(cancelButton);

    expect(setOpenMock).toHaveBeenCalledTimes(2);
    expect(handleConfirmMock).not.toHaveBeenCalled();
  });
});
