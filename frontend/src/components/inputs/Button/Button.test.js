import { afterEach, beforeEach, describe, expect, it, test, vi } from "vitest";
import userEvent from '@testing-library/user-event';
import { render, cleanup, screen } from "@testing-library/svelte";

import Button from "./Button.svelte";
import ButtonStory from "./ButtonStory.svelte";


describe("Button", () => {
    afterEach(() => cleanup())

    it("should call handleClick func", async () => {
        const user = userEvent.setup();
        const handleClickMock = vi.fn();

        render(Button, { handleClick: handleClickMock });

        const button = screen.getByRole('button');
        await user.click(button);

        expect(handleClickMock).toHaveBeenCalledOnce();
    })

    it("should not allow click if disabled", async () => {
        const user = userEvent.setup();
        const handleClickMock = vi.fn();

        render(Button, { handleClick: handleClickMock, disabled: true });

        const button = screen.getByRole('button');
        await user.click(button);

        expect(handleClickMock).not.toHaveBeenCalled();
    })

    it("should have aria pressed if highlighted", async () => {
        render(Button, { highlighted: true });

        const button = screen.getByRole('button');
        expect(button.getAttribute("aria-pressed")).toBeTruthy("true");
    })

    it("should aria pressed if highlighted is passed but false", async () => {
        render(Button, { highlighted: false });

        const button = screen.getByRole('button');
        expect(button.getAttribute("aria-pressed")).toEqual("false");
    })

    it("should render story", () => {
        render(ButtonStory);
    })
})