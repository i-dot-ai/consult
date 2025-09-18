import { afterEach, beforeEach, describe, expect, it, test, vi } from "vitest";
import userEvent from '@testing-library/user-event';
import { render, cleanup, screen } from "@testing-library/svelte";

import Star from "../../svg/material/Star.svelte";
import RespondentSidebarItem from "./RespondentSidebarItem.svelte";
import RespondentSidebarItemStory from "./RespondentSidebarItemStory.svelte";


let testData;

describe("RespondentSidebarItem", () => {
    beforeEach(() => {
        testData = {
            title: "Test Item",
            subtitle: "This is a test item",
            icon: Star,
        };
    })

    afterEach(() => cleanup())

    it("should render data", () => {
        const { getByText, container } = render(RespondentSidebarItem, {
            ...testData,
        });

        expect(getByText(testData.title));
        expect(getByText(testData.subtitle));
        expect(container.querySelector("svg")).toBeTruthy();
    })

    it("should render editable mode and all update callback", async () => {
        vi.mock("svelte/transition");
        const user = userEvent.setup();
        const updateSubtitleMock = vi.fn();

        const {
            getByTestId,
            queryByTestId,
            queryByLabelText,
            getByLabelText,
        } = render(RespondentSidebarItem, {
            ...testData,
            editable: true,
            updateSubtitle: updateSubtitleMock,
        });

        // button hidden initially
        expect(queryByTestId("save-button")).toBeNull();
        expect(queryByTestId("cancel-button")).toBeNull();
        expect(queryByLabelText("Edit Subtitle")).toBeNull();

        // click to reveal buttons and text input
        const editButton = getByTestId("edit-button");
        await user.click(editButton);

        // clear existing subtitle and type new one
        const subtitleInput = getByLabelText("Edit Subtitle");
        await user.clear(subtitleInput);
        await user.type(subtitleInput, "New Subtitle");

        // click to save subtitle
        const saveButton = getByTestId("save-button");
        await user.click(saveButton);

        // check if subtitle is updated correctly
        expect(updateSubtitleMock).toHaveBeenCalledWith("New Subtitle");
    })

    it("should reset staged subtitle if cancel is clicked", async () => {
        vi.mock("svelte/transition");
        const user = userEvent.setup();
        const updateSubtitleMock = vi.fn();

        const {
            getByText,
            getByTestId,
            queryByLabelText,
            getByLabelText,
        } = render(RespondentSidebarItem, {
            ...testData,
            editable: true,
            updateSubtitle: updateSubtitleMock,
        });

        // click to reveal buttons and text input
        const editButton = getByTestId("edit-button");
        await user.click(editButton);

        // clear existing subtitle and type new one
        let subtitleInput = getByLabelText("Edit Subtitle");
        await user.clear(subtitleInput);
        await user.type(subtitleInput, "New Subtitle");

        // click to cancel edit
        const cancelButton = getByTestId("cancel-button");
        await user.click(cancelButton);

        // text input should disappear at this point
        expect(queryByLabelText("Edit Subtitle")).toBeNull();

        // check that old subtitle is displayed still
        expect(getByText(testData.subtitle));

        // check that update callback never been called
        expect(updateSubtitleMock).not.toHaveBeenCalled();

        // re-enable edit mode and check that staged subtitle is reset
        await user.click(editButton);
        subtitleInput = getByLabelText("Edit Subtitle");
        expect(subtitleInput.value).toBe(testData.subtitle);
    })

    it("should render story", () => {
        render(RespondentSidebarItemStory);
    })
})