import { afterEach, beforeEach, describe, expect, it, test, vi } from "vitest";
import userEvent from '@testing-library/user-event';
import { render, cleanup, screen } from "@testing-library/svelte";

import Switch from "./Switch.svelte";


describe("Switch", () => {
    afterEach(() => cleanup())

    it("should call handleChange func", async () => {
        const user = userEvent.setup();
        const handleChangeMock = vi.fn();

        render(Switch, {
            id: "test-switch",
            value: false,
            label: "Test Switch",
            handleChange: handleChangeMock
        });


        const button = screen.getByRole('switch');

        expect(handleChangeMock).toHaveBeenCalledTimes(1);

        await user.click(button);

        expect(handleChangeMock).toHaveBeenCalledTimes(2);
    })

    it("should have correct attributes when switched", async () => {
        const user = userEvent.setup();
        const handleChangeMock = vi.fn();

        render(Switch, {
            id: "test-switch",
            value: false,
            label: "Test Switch",
            handleChange: handleChangeMock
        });


        const button = screen.getByRole('switch');

        expect(button.getAttribute("data-state")).toEqual("unchecked");
        expect(button.getAttribute("aria-checked")).toEqual("false");

        await user.click(button);

        expect(button.getAttribute("data-state")).toEqual("checked");
        expect(button.getAttribute("aria-checked")).toEqual("true");
    })

    it("should have render props", async () => {
        const handleChangeMock = vi.fn();

        const {container, getByLabelText} = render(Switch, {
            id: "test-switch",
            value: false,
            label: "Test Switch",
            handleChange: handleChangeMock,
        });

        expect(container.querySelector("#test-switch")).toBeTruthy();
        expect(container.querySelector(`#test-switch-label[for="test-switch"]`)).toBeTruthy();
        expect(getByLabelText("Test Switch"));
    })

    it("should have be checked initially if value is true", async () => {
        const handleChangeMock = vi.fn();

        render(Switch, {
            id: "test-switch",
            value: true,
            label: "Test Switch",
            handleChange: handleChangeMock,
        });
        const button = screen.getByRole('switch');
        expect(button.getAttribute("data-state")).toEqual("checked");
    })
})