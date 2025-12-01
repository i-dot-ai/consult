import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";

import CsvDownload from "./CsvDownload.svelte";
import { getPercentage } from "../../global/utils";

describe("CsvDownload", () => {
  const data = [{ foo: 1, bar: 2 }];
  const fileName = "test.csv";

  it("should render data inside href for downloading", () => {
    render(CsvDownload, { data, fileName });

    const el = screen.getByTestId("csv-download");
    const decoded = atob(el.href.split(",")[1]);
    expect(decoded).toEqual("foo,bar\n1,2");
    expect(el.download).toEqual(fileName);
  });

  it("should default to a filename if none provided", () => {
    render(CsvDownload, { data });

    const el = screen.getByTestId("csv-download");
    expect(el.download).toEqual("data.csv");
  });

  it("should not crash if no data is passed", () => {
    render(CsvDownload);

    const el = screen.getByTestId("csv-download");
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
