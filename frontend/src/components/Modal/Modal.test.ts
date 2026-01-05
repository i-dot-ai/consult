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
    render(Modal, testData);

    expect(screen.queryByText("Ok")).toBeNull();
    expect(screen.queryByText("Child Element")).toBeNull();
  });

  it("should render contents if open", async () => {
    const handleConfirmMock = vi.fn();
    const setOpenMock = vi.fn();

    expect(testData).toBeTruthy();
    render(Modal, {
      ...testData,
      open: true,
      handleConfirm: handleConfirmMock,
      setOpen: setOpenMock,
    });

    expect(screen.getByText("Child Element")).toBeInTheDocument();
    expect(screen.getByText(testData.title)).toBeInTheDocument();
    expect(screen.getByText(testData.confirmText)).toBeInTheDocument();
  });

  it("should close when close button is clicked", async () => {
    const handleConfirmMock = vi.fn();
    const setOpenMock = vi.fn();

    expect(testData).toBeTruthy();
    render(Modal, {
      ...testData,
      open: true,
      handleConfirm: handleConfirmMock,
      setOpen: setOpenMock,
    });

    expect(screen.getByText("Child Element")).toBeInTheDocument();
    expect(setOpenMock).toHaveBeenCalledTimes(1);
    const cancelButton = screen.getByText("Cancel");

    await fireEvent.click(cancelButton);

    expect(screen.queryByText("Child Element")).not.toBeInTheDocument();
    expect(setOpenMock).toHaveBeenCalledTimes(2);
  });

  it("should call confirm callback when clicked", async () => {
    const handleConfirmMock = vi.fn();
    const setOpenMock = vi.fn();

    expect(testData).toBeTruthy();
    render(Modal, {
      ...testData,
      open: true,
      handleConfirm: handleConfirmMock,
      setOpen: setOpenMock,
    });

    expect(screen.getByText("Ok")).toBeInTheDocument();
    const confirmButton = screen.getByText("Ok");

    await fireEvent.click(confirmButton);

    expect(setOpenMock).toHaveBeenCalledOnce();
    expect(handleConfirmMock).toHaveBeenCalledOnce();
  });

  it("should not call confirm callback when cancel is clicked", async () => {

    const handleConfirmMock = vi.fn();
    const setOpenMock = vi.fn();

    expect(testData).toBeTruthy();
    render(Modal, {
      ...testData,
      handleConfirm: handleConfirmMock,
      open: true,
      setOpen: setOpenMock,
    });

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
