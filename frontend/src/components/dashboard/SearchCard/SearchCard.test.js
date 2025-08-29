import { afterEach, beforeEach, describe, expect, it, test } from "vitest";
import { render, cleanup } from "@testing-library/svelte";

import SearchCardTest from "./SearchCardTest.svelte";


let testData;

describe("SearchCard", () => {
    beforeEach(() => {
        testData = {
            title: "Test Title",
            description: "Test Description",
            tags: ["tag 1", "tag 2"],
            footerContent: "Footer Content",
            asideContent: "Aside Content",
        };
    })

    afterEach(() => cleanup())

    it("should render data", () => {
        const { getByText } = render(SearchCardTest, {
            title: testData.title,
            description: testData.description,
            tags: testData.tags,
            footerContent: testData.footerContent,
            asideContent: testData.asideContent,
        });

        expect(getByText(testData.title));
        expect(getByText(testData.description));
        expect(getByText(testData.footerContent));
        expect(getByText(testData.asideContent));
        testData.tags.forEach(tag => expect(getByText(tag)));
    })

    it("should render data", () => {
        const { container, getByText } = render(SearchCardTest, {
            title: testData.title,
            description: testData.description,
            tags: testData.tags,
            footerContent: testData.footerContent,
            asideContent: testData.asideContent,
        });

        expect(getByText(testData.title));
        expect(getByText(testData.description));
        expect(getByText(testData.footerContent));
        expect(getByText(testData.asideContent));
        testData.tags.forEach(tag => expect(getByText(tag)));
        expect(container.querySelector("span.bg-yellow-300")).toBeNull();
    })

    it("should highlight text if highlightText is passed", () => {
        const HIGHLIGHT_TEXT = "Description";

        const { container } = render(SearchCardTest, {
            title: testData.title,
            description: testData.description,
            tags: testData.tags,
            footerContent: testData.footerContent,
            asideContent: testData.asideContent,
            highlightText: HIGHLIGHT_TEXT,
        });

        expect(container.querySelector("span.bg-yellow-300").innerHTML).toEqual(HIGHLIGHT_TEXT);
    })
})