import { afterEach, beforeEach, describe, expect, it, test } from "vitest";
import { render, cleanup, screen } from "@testing-library/svelte";

import QuestionSummary from "./QuestionSummary.svelte";


let testData;

describe("QuestionSummary", () => {
    beforeEach(() => {
        testData = {
            themesLoading: false,
        };
    })

    afterEach(() => cleanup())

    it("should render data", () => {
        const { getByText } = render(QuestionSummary, {});

        expect(getByText("Theme analysis"));
        expect(getByText("Analysis of key themes mentioned in responses to this question."));
    })

    it("should render multi choice data if passed", () => {
        const multiChoice = { "": { "yes": 10, "no": 20 } };

        const { getByText } = render(QuestionSummary, {
            multiChoice: multiChoice,
            themesLoading: testData.themesLoading,
        });

        expect(getByText("Multiple Choice Answers"));

        // TODO: enable after porting iai-progress-card to Svelte
        // ---
        // Object.keys(multiChoice).forEach(key => {
        //     Object.keys(multiChoice[key]).forEach(answerKey => {
        //         expect(getByText(answerKey));
        //         expect(getByText(multiChoice[key][answerKey]));
        //     })
        // })
    })
})