import { describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { render, screen } from "@testing-library/svelte";

import Star from "../../svg/material/Star.svelte";
import RespondentSidebarItem from "./RespondentSidebarItem.svelte";

describe("RespondentSidebarItem", () => {
  const testData = {
    title: "Test Item",
    subtitle: "This is a test item",
    icon: Star,
  };

  it("should render data", () => {
    render(RespondentSidebarItem, testData);

    expect(screen.getByText(testData.title)).toBeInTheDocument();
    expect(screen.getByText(testData.subtitle)).toBeInTheDocument();
  });

  it("should render editable mode and all update callback", async () => {
    const user = userEvent.setup();
    const updateSubtitleMock = vi.fn();

    render(RespondentSidebarItem, {
      ...testData,
      editable: true,
      updateSubtitle: updateSubtitleMock,
    });

    // button hidden initially
    expect(screen.queryByTestId("save-button")).toBeNull();
    expect(screen.queryByTestId("cancel-button")).toBeNull();
    expect(screen.queryByLabelText("Edit Subtitle")).toBeNull();

    // click to reveal buttons and text input
    const editButton = screen.getByTestId("edit-button");
    await user.click(editButton);

    // clear existing subtitle and type new one
    const subtitleInput = screen.getByLabelText("Edit Subtitle");
    await user.clear(subtitleInput);
    await user.type(subtitleInput, "New Subtitle");

    // click to save subtitle
    const saveButton = screen.getByTestId("save-button");
    await user.click(saveButton);

    // check if subtitle is updated correctly
    expect(updateSubtitleMock).toHaveBeenCalledWith("New Subtitle");
  });

  it("should reset staged subtitle if cancel is clicked", async () => {
    const user = userEvent.setup();
    const updateSubtitleMock = vi.fn();

    render(RespondentSidebarItem, {
      ...testData,
      editable: true,
      updateSubtitle: updateSubtitleMock,
    });

    // click to reveal buttons and text input
    const editButton = screen.getByTestId("edit-button");
    await user.click(editButton);

    // clear existing subtitle and type new one
    let subtitleInput = screen.getByLabelText(
      "Edit Subtitle",
    ) as HTMLInputElement;
    await user.clear(subtitleInput);
    await user.type(subtitleInput, "New Subtitle");

    // click to cancel edit
    const cancelButton = screen.getByTestId("cancel-button");
    await user.click(cancelButton);

    // text input should disappear at this point
    expect(screen.queryByLabelText("Edit Subtitle")).toBeNull();

    // check that old subtitle is displayed still
    expect(screen.getByText(testData.subtitle)).toBeInTheDocument();

    // check that update callback never been called
    expect(updateSubtitleMock).not.toHaveBeenCalled();

    // re-enable edit mode and check that staged subtitle is reset
    await user.click(editButton);
    subtitleInput = screen.getByLabelText("Edit Subtitle") as HTMLInputElement;
    expect(subtitleInput.value).toBe(testData.subtitle);
  });
});
