import { describe, expect, it } from "vitest";
import { createRawSnippet }from "svelte"
import { render } from "@testing-library/svelte";

import Text from "./Text.svelte";


describe("Text", () => {
    it("renders correct text", () => {
        const content = "This is some text"
        const childComponent = createRawSnippet(() => {
            return {
                render: () => content,
            };
        });
        const { getByText } = render(Text, { children: childComponent });

        expect(getByText(content)).toBeTruthy();
    })
})