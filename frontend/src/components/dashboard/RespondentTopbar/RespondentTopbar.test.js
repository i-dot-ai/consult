import { afterEach, beforeEach, describe, expect, it, test, vi } from "vitest";
import userEvent from '@testing-library/user-event';
import { render, cleanup, screen } from "@testing-library/svelte";

import RespondentTopbar from "./RespondentTopbar.svelte";
import RespondentTopbarStory from "./RespondentTopbarStory.svelte";


let testData;

describe("RespondentTopbar", () => {
    beforeEach(() => {
        testData = {
            respondentId: "test-respondent",
            backUrl: "#",
        };
    })

    afterEach(() => cleanup())

    it("should render data and links", () => {
        const { getByText, container } = render(RespondentTopbar, {
            ...testData,
        });

        expect(getByText(`Respondent ${testData.respondentId}`));
        expect(getByText("Back to Analysis"));
        expect(getByText("Previous Respondent"));
        expect(getByText("Next Respondent"));        
    })

    it("should render story", () => {
        render(RespondentTopbarStory);
    })
})