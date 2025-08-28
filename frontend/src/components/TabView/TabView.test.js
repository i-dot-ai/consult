import { afterEach, beforeEach, describe, expect, it, test, vi } from "vitest";
import userEvent from '@testing-library/user-event';
import { render, cleanup, screen } from "@testing-library/svelte";

import TabView from "./TabView.svelte";
import Star from "../svg/material/Star.svelte";
import Finance from "../svg/material/Finance.svelte";


describe("TabView", () => {
    afterEach(() => cleanup())

    it("should call handleClick func", async () => {
        const user = userEvent.setup();
        const handleChangeMock = vi.fn();

        const { container } = render(TabView, {
            value: "star-tab",
            tabs: [
                { id: "star-tab", title: "Star Tab", icon: Star},
                { id: "finance-tab", title: "Finance Tab", icon: Finance},
            ],
            handleChange: handleChangeMock,
        });

        expect(screen.getByText("Star Tab"));
        expect(screen.getByText("Finance Tab"));
        expect(container.querySelectorAll("svg")).toHaveLength(2);

        const tabButtons = await screen.findAllByRole('tab');
        const starTab = tabButtons.at(0);
        const financeTab = tabButtons.at(1);
        await user.click(financeTab);

        expect(handleChangeMock).toHaveBeenCalledTimes(2);
        expect(handleChangeMock).toHaveBeenCalledWith("finance-tab");

        await user.click(starTab);
        expect(handleChangeMock).toHaveBeenCalledTimes(4);
        expect(handleChangeMock).toHaveBeenCalledWith("star-tab");
    })

    it("should not render icons if no icon is passed", async () => {
        const { container } = render(TabView, {
            value: "star-tab",
            tabs: [
                { id: "star-tab", title: "Star Tab" },
                { id: "finance-tab", title: "Finance Tab" },
            ],
        });

        expect(container.querySelectorAll("svg")).toHaveLength(0);
    })
})