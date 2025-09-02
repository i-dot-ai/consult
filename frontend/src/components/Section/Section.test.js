import { describe, expect, it, test } from "vitest";
import { render } from "@testing-library/svelte";

import SectionTest from "./SectionTest.svelte";


describe("Section", () => {
    it("should render", () => {
        const { getByText } = render(SectionTest);
        expect(getByText("Test Slot"));
    })
})