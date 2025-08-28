import { afterEach, beforeEach, describe, expect, it, test } from "vitest";
import { render, cleanup, screen } from "@testing-library/svelte";

import PanelTest from "./PanelTest.svelte";


describe("Panel", () => {
    afterEach(() => cleanup())

    it("should render slot", () => {
        const { getByText } = render(PanelTest, { slot: "<p>Slot Content</p>" });

        expect(getByText("Slot Content"));
    })

    it("should render correct css based on props", () => {
        const { getByTestId } = render(PanelTest, {
            slot: "<p>Slot Content</p>",
            border: true,
            bg: true,
        });

        const panel = getByTestId("panel-component");
        expect(panel.getAttribute("class")).toContain("border");
        expect(panel.getAttribute("class")).toContain("bg-");
    })

    it.each([1, 2, 3])("should render correctly for each level", (level) => {
        render(PanelTest, {
            slot: "<p>Slot Content</p>",
            level: level,
        });
    })
})