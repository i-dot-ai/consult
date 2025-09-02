import { afterEach, beforeEach, describe, expect, it, test } from "vitest";
import { render, cleanup, screen } from "@testing-library/svelte";

import ResponseAnalysis from "./ResponseAnalysis.svelte";


let testData;

describe("ResponseAnalysis", () => {
    beforeEach(() => {
        testData = {};
    })

    afterEach(() => cleanup())

    it("should render data", () => {
        const { getByText } = render(ResponseAnalysis, {});

        expect(getByText("Response refinement"));
        expect(getByText("In-depth analysis of individual consultation responses."));
    })
})