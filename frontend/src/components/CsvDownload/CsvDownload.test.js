import { afterEach, beforeEach, describe, expect, it, test } from "vitest";
import { cleanup, render, screen } from "@testing-library/svelte";

import CsvDownload from "./CsvDownload.svelte";
import { getPercentage } from "../../global/utils";

let testData;

describe("CsvDownload", () => {
  beforeEach(() => {
    testData = [{ foo: 1, bar: 2 }];
  });

  afterEach(() => {
    cleanup();
  });

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
  });

  it("should default to a filename if none provided", () => {
    const { getByTestId } = render(CsvDownload, {
      data: testData,
    });

    const el = getByTestId("csv-download");
    expect(el.download).toEqual("data.csv");
  });

  it("should not crash if no data is passed", () => {
    const { getByTestId } = render(CsvDownload);

    const el = getByTestId("csv-download");
    expect(el.href).toEqual("data:text/csv;base64,");
  });

  it("should not fail on chars outside of latin-1 range", () => {
    const TEST_DATA = {
      themes: [
        {
          id: "test-theme",
          name: "Test Theme",
          description: "Invalid char: ’ ",
        },
      ],
    };

    expect(() => {
      render(CsvDownload, {
        data: TEST_DATA.themes.map((theme) => ({
          "Theme Name": theme.name,
          "Theme Description": theme.description,
          Mentions: theme.count,
          Percentage: getPercentage(theme.count, 100),
        })),
      });
    }).not.toThrowError();

    // Confirm this indeed is an invalid char
    expect(() => btoa(" ’ ")).toThrowError();
  });
});
