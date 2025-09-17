import { afterEach, beforeEach, describe, expect, it, test } from "vitest";
import { render, cleanup, screen } from "@testing-library/svelte";

import RespondentAnswer from "./RespondentAnswer.svelte";


let testData;

describe("RespondentAnswer", () => {
    beforeEach(() => {
        testData = {
            questionTitle: "Do you agree with the proposal to align the flavour categories of chocolate bars as outlined in the draft guidelines of the Chocolate Bar Regulation for the United Kingdom?",
            questionNumber: 1,
            answerText: "I agree in principle, but I think the guidelines should include a provision for periodic review to adapt to market changes.",
            themes: [ "Innovation", "Standardized framework" ],
            evidenceRich: true,
        };
    })

    afterEach(() => cleanup())

    it("should render data", () => {
        const { getByText } = render(RespondentAnswer, {
            questionTitle: testData.questionTitle,
            questionNumber: testData.questionNumber,
            answerText: testData.answerText,
            themes: testData.themes,
            evidenceRich: testData.evidenceRich,
        });

        expect(getByText(testData.questionTitle));
        expect(getByText(`Q${testData.questionNumber}`));
        expect(getByText(testData.answerText));
        testData.themes.forEach(theme => expect(getByText(theme)));
        expect(getByText("Evidence-rich"));
    })

    it("should not fail if no themes presenet", () => {
        expect(() => {
            render(RespondentAnswer, {
                questionTitle: testData.questionTitle,
                questionNumber: testData.questionNumber,
                answerText: testData.answerText,
                themes: [],
                evidenceRich: testData.evidenceRich,
            });
        }).not.toThrow();
    })

    it("should not render evidence rich tag if not evidence rich", () => {
        const { queryByText } = render(RespondentAnswer, {
            questionTitle: testData.questionTitle,
            questionNumber: testData.questionNumber,
            answerText: testData.answerText,
            themes: testData.themes,
            evidenceRich: false,
        });

        expect(queryByText("Evidence-rich")).toBeNull();
    })
})