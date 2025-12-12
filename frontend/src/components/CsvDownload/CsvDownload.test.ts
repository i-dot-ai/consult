import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";

import CsvDownload from "./CsvDownload.svelte";

describe("CsvDownload", () => {
  const data = [{ foo: 1, bar: 2 }];
  const fileName = "test.csv";

  it("should render data inside href for downloading", () => {
    render(CsvDownload, { data, fileName });

    const el: HTMLAnchorElement = screen.getByTestId("csv-download");
    const decoded = atob(el.href.split(",")[1]);
    expect(decoded).toEqual("foo,bar\n1,2");
    expect(el.download).toEqual(fileName);
  });

  it("should default to a filename if none provided", () => {
    render(CsvDownload, { data });

    const el: HTMLAnchorElement = screen.getByTestId("csv-download");
    expect(el.download).toEqual("data.csv");
  });

  it("should not crash if no data is passed", () => {
    render(CsvDownload);

    const el: HTMLAnchorElement = screen.getByTestId("csv-download");
    expect(el.href).toEqual("data:text/csv;base64,");
  });

  it("should not fail on chars outside of latin-1 range", () => {
    expect(() => {
      render(CsvDownload, {
        data: [
          {
            "Theme Name": "Test Theme",
            "Theme Description": "Invalid char: ’ ",
          },
        ],
      });
    }).not.toThrowError();

    // Confirm this indeed is an invalid char
    expect(() => btoa(" ’ ")).toThrowError();
  });
});
