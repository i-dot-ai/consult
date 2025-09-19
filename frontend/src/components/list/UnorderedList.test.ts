import { describe, expect, it } from "vitest";
import { createRawSnippet }from "svelte"
import { render } from "@testing-library/svelte";

import UnorderedList from "./UnorderedList.svelte";

describe("UnorderedList", () => {
    it("renders list", () => {
        const listItem = `<li>This is a list item</li>`;
        const childComponent = createRawSnippet(() => {
            return {
                render: () => listItem,
            };
        });
        const { getByText } = render(UnorderedList, { children: childComponent });

        expect(getByText("This is a list item")).toBeTruthy();
    })
});