import { afterEach, beforeEach, describe, expect, it, test, vi } from "vitest";
import userEvent from '@testing-library/user-event';
import { render, cleanup, screen } from "@testing-library/svelte";

import { createRawSnippet } from "svelte";

import RespondentTopbar from "./RespondentTopbar.svelte";
import RespondentTopbarStory from "./RespondentTopbarStory.svelte";


let testData;

describe("RespondentTopbar", () => {
    beforeEach(() => {
      testData = {
          title: "test-title",
          backUrl: "#",
      };
    })

    afterEach(() => cleanup())

    it("should render data and links", () => {
        const { getByText, container } = render(RespondentTopbar, {
            ...testData,
        });

        expect(getByText(testData.title));
        expect(getByText("Back to Analysis"));    
    })

    it("should render child", () => {
        const { getByText, container } = render(RespondentTopbar, {
            ...testData,
            children: createRawSnippet(() => ({
              render: () => `<p>Child content</p>`,
            }))
        });

        expect(getByText(`Child content`));
    })

    it("should render story", () => {
        render(RespondentTopbarStory);
    })
})