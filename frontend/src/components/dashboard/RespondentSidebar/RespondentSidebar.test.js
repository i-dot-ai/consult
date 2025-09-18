import { afterEach, beforeEach, describe, expect, it, test, vi } from "vitest";
import userEvent from '@testing-library/user-event';
import { render, cleanup, screen } from "@testing-library/svelte";

import RespondentSidebar from "./RespondentSidebar.svelte";
import RespondentSidebarStory from "./RespondentSidebarStory.svelte";
import { getPercentage } from "../../../global/utils";


let testData;

describe("RespondentSidebar", () => {
    beforeEach(() => {
        testData = {
            respondentType: "Test type",
            geographicLocation: "Test location",
            selfReportedDisability: "Test disability",
            sector: "Test sector",
            stakeholderName: "Test stakeholder",
            questionsAnswered: 10,
            totalQuestions: 20,
        };
    })

    afterEach(() => cleanup())

    it("should render data", () => {
        const { getByText, container } = render(RespondentSidebar, {
            ...testData,
        });

        expect(getByText(testData.respondentType));
        expect(getByText(testData.geographicLocation));
        expect(getByText(testData.selfReportedDisability));
        expect(getByText(testData.sector));
        expect(getByText(testData.stakeholderName));
        
        const partialNum = testData.questionsAnswered;
        const totalNum = testData.totalQuestions;
        const percentage = getPercentage(partialNum, totalNum);
        const countsText = `${percentage}% (${partialNum}/${totalNum})`;
        expect(getByText(countsText));
    })

    it("should render editable mode and call update callback", async () => {
        vi.mock("svelte/transition");
        const user = userEvent.setup();
        const updateMock = vi.fn();

        const {
            getByTestId,
            getByLabelText,
        } = render(RespondentSidebar, {
            ...testData,
            updateStakeholderName: updateMock,
        });

        // click to reveal buttons and text input
        const editButton = getByTestId("edit-button");
        await user.click(editButton);

        // clear existing subtitle and type new one
        const subtitleInput = getByLabelText("Edit Subtitle");
        await user.clear(subtitleInput);
        await user.type(subtitleInput, "New Stakeholder");

        // click to save subtitle
        const saveButton = getByTestId("save-button");
        await user.click(saveButton);

        // check if subtitle is updated correctly
        expect(updateMock).toHaveBeenCalledWith("New Stakeholder");
    })

    it("should render story", () => {
        render(RespondentSidebarStory);
    })
})