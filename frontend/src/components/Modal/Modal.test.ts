import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/svelte";

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
    };
  });

  it("does not render contents if closed", async () => {
    const { component } = render(Modal, {
      ...testData,
    });

    // store does not update without this
    await act(() => component.setImperativeOpen(false));

    expect(screen.queryByText("Ok")).toBeNull();
    expect(screen.queryByText("Child Element")).toBeNull();
  });

  it("should render contents if open", async () => {
    const handleConfirmMock = vi.fn();
    const setOpenMock = vi.fn();

    expect(testData).toBeTruthy();
    const { component } = render(Modal, {
      ...testData,
      handleConfirm: handleConfirmMock,
      setOpen: setOpenMock,
    });

    // store does not update without this
    await act(() => component.setImperativeOpen(true));

    expect(screen.getByText("Child Element")).toBeInTheDocument();
    expect(screen.getByText(testData.title)).toBeInTheDocument();
    expect(screen.getByText(testData.confirmText)).toBeInTheDocument();
  });

  it("should call confirm callback when clicked", async () => {
    vi.mock("svelte/transition");

    const handleConfirmMock = vi.fn();
    const setOpenMock = vi.fn();

    expect(testData).toBeTruthy();
    const { component } = render(Modal, {
      ...testData,
      handleConfirm: handleConfirmMock,
      setOpen: setOpenMock,
    });

    // store does not update without this
    await act(() => component.setImperativeOpen(true));

    expect(screen.getByText("Ok")).toBeInTheDocument();
    const confirmButton = screen.getByText("Ok");

    await fireEvent.click(confirmButton);

    expect(setOpenMock).toHaveBeenCalledOnce();
    expect(handleConfirmMock).toHaveBeenCalledOnce();
  });

  it("should not call confirm callback when cancel is clicked", async () => {
    vi.mock("svelte/transition");

    const handleConfirmMock = vi.fn();
    const setOpenMock = vi.fn();

    expect(testData).toBeTruthy();
    const { component } = render(Modal, {
      ...testData,
      handleConfirm: handleConfirmMock,
      setOpen: setOpenMock,
    });

    // store does not update without this - TODO: Fix meltOpen update
    await act(() => component.setImperativeOpen(true));

    expect(screen.getByText("Ok")).toBeInTheDocument();
    const cancelButton = screen.getByText("Cancel");

    await fireEvent.click(cancelButton);

    expect(setOpenMock).toHaveBeenCalledTimes(2);
    expect(handleConfirmMock).not.toHaveBeenCalled();
  });

  it("matches snapshot", () => {
    const { container } = render(Modal, testData);

    expect(container).toMatchSnapshot();
  });
});
