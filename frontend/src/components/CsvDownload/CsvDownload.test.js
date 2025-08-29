import { afterEach, beforeEach, describe, expect, it, test } from "vitest";
import { cleanup, render, screen } from "@testing-library/svelte";

import CsvDownload from "./CsvDownload.svelte";


let testData;

describe("CsvDownload", () => {
    beforeEach(() => {
        testData = [{"foo": 1, "bar": 2}];
    })

    afterEach(() => {
        cleanup();
    })

    it("should render data inside href for downloading", () => {
        const TEST_FILENAME = "test.csv";

        const { getByTestId } = render(CsvDownload, {
            data: testData,
            fileName: TEST_FILENAME,
        });

        const el = getByTestId("csv-download");
        const decoded = atob(el.href.split(",")[1]);
        expect(decoded).toEqual("foo,bar\n1,2");
        expect(el.download).toEqual(TEST_FILENAME);
    })

    it("should default to a filename if none provided", () => {
        const { getByTestId } = render(CsvDownload, {
            data: testData,
        });

        const el = getByTestId("csv-download");
        expect(el.download).toEqual("data.csv");
    })

    it("should not crash if no data is passed", () => {
        const { getByTestId } = render(CsvDownload);

        const el = getByTestId("csv-download");
        expect(el.href).toEqual("data:text/csv;base64,");
    })
})