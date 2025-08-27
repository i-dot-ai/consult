import { afterEach, beforeEach, describe, expect, it, test } from "vitest";
import { render, cleanup } from "@testing-library/svelte";

import AnswerCard from "./AnswerCard.svelte";


let testData;

describe("AnswerCard", () => {
    beforeEach(() => {
        testData = {
            id: "TEST-ID",
            text: "Test answer",
            demoData: ["demo 1", "demo 2"],
            multiAnswers: ["multi 1", "multi 2"],
            evidenceRich: true,
            themes: [{ name: "theme 1" }, { name: "theme 2" }],
        };
    })

    afterEach(() => cleanup())

    it("should render data", () => {
        const { getByText } = render(AnswerCard, {
            id: testData.id,
            text: testData.text,
            demoData: testData.demoData,
            multiAnswers: testData.multiAnswers,
            evidenceRich: testData.evidenceRich,
            themes: testData.themes,
        });

        expect(getByText(`ID: ${testData.id}`));
        expect(getByText(testData.text));
        testData.demoData.forEach(data => expect(getByText(data)));
        testData.multiAnswers.forEach(multi => expect(getByText(multi)));
        testData.themes.forEach(theme => expect(getByText(theme.name)));
        expect(getByText("Evidence-rich"));
    })

    it("should not render data if skeleton", async () => {
        const { queryByText } = render(AnswerCard, {
            id: testData.id,
            text: testData.text,
            demoData: testData.demoData,
            multiAnswers: testData.multiAnswers,
            evidenceRich: testData.evidenceRich,
            themes: testData.themes,
            skeleton: true,
        });

        expect(queryByText(`ID: ${testData.id}`)).toBeNull();
        expect(queryByText(testData.text)).toBeNull();
        expect(queryByText("Evidence-rich")).toBeNull();
        testData.themes.forEach(theme => expect(queryByText(theme.name)).toBeNull());
        testData.multiAnswers.forEach(multi => expect(queryByText(multi)).toBeNull());
        testData.demoData.forEach(demo => expect(queryByText(demo)).toBeNull());
    })

    it("should highlight text if passed", async () => {
        const HIGHLIGHT_TEXT = "answer";
        const { container } = render(AnswerCard, {
            id: testData.id,
            text: testData.text,
            demoData: testData.demoData,
            multiAnswers: testData.multiAnswers,
            evidenceRich: testData.evidenceRich,
            themes: testData.themes,
            highlightText: HIGHLIGHT_TEXT,
        });

        expect(container.querySelector("span.bg-yellow-300").innerHTML).toEqual(HIGHLIGHT_TEXT);
    })
})