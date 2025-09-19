import { afterEach, beforeEach, describe, expect, it, test } from "vitest";
import { render, cleanup, screen } from "@testing-library/svelte";

import { createRawSnippet } from 'svelte';

import PanelStory from "./PanelStory.svelte";
import Panel from "./Panel.svelte";


let childComponent;

describe("Panel", () => {
    beforeEach(() => {
        childComponent = createRawSnippet(() => {
            return {
                render: () => "<p>Child Content</p>",
            };
        });
    })
    afterEach(() => cleanup())

    it("should render slot", () => {
        const { getByText } = render(Panel, { children: childComponent });

        expect(getByText("Child Content"));
    })

    it("should render correct css based on props", () => {
        const { getByTestId } = render(Panel, {
            border: true,
            bg: true,
            children: childComponent,
        });

        const panel = getByTestId("panel-component");
        expect(panel.getAttribute("class")).toContain("border");
        expect(panel.getAttribute("class")).toContain("bg-");
    })

    it.each([1, 2, 3])("should render correctly for each level", (level) => {
        render(Panel, {
            level: level,
            children: childComponent,
        });
    })

    it("should render story", () => {
        render(PanelStory);
    })
})