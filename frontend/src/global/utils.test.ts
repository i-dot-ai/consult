import { describe, expect, it } from "vitest";
import {
  applyHighlight,
  formatDate,
  formatTimeDeltaText,
  getEnv,
  getPercentage,
  getTimeDeltaInMinutes,
  toTitleCase,
} from "./utils";

describe("getPercentage", () => {
  it("correctly calculates percentages", () => {
    const result = getPercentage(100, 1000);
    expect(result).toEqual(10);
  });
  it("correctly calculates when partial value is negative", () => {
    const result = getPercentage(-100, 1000);
    expect(result).toEqual(-10);
  });
  it("correctly calculates when both values are negative", () => {
    const result = getPercentage(-100, -1000);
    expect(result).toEqual(10);
  });
  it("returns 0 if partial value is 0", () => {
    const result = getPercentage(0, 1000);
    expect(result).toEqual(0);
  });
  it("returns 0 if total value is 0", () => {
    const result = getPercentage(10, 0);
    expect(result).toEqual(0);
  });
  it("returns 0 if both values are 0", () => {
    const result = getPercentage(0, 0);
    expect(result).toEqual(0);
  });
});

describe("toTitleCase", () => {
  it("converts to title case", () => {
    expect(toTitleCase("test string")).toEqual("Test String");
  });
  it("removes hyphens", () => {
    expect(toTitleCase("test-string")).toEqual("Test String");
  });
  it("handles empty strings", () => {
    expect(toTitleCase("")).toEqual("");
  });
});

describe("applyHighlight", () => {
  it("wraps highlighted text inside span", () => {
    const result = applyHighlight("Full test text", "test");
    expect(result).toContain(`<span class="bg-yellow-300">test</span>`);
  });
  it("handles upper and lower cases", () => {
    const result = applyHighlight("full TeSt text", "test");
    expect(result).toContain(`<span class="bg-yellow-300">TeSt</span>`);
  });
});

describe("getEnv", () => {
  it("returns correct env for dev", () => {
    const result = getEnv("consult-dev.ai.cabinetoffice.gov.uk");
    expect(result).toEqual("dev");
  });
  it("returns correct env for prod", () => {
    const result = getEnv("consult.ai.cabinetoffice.gov.uk");
    expect(result).toEqual("prod");
  });
  it("returns correct env for local", () => {
    const result = getEnv("localhost:3000");
    expect(result).toEqual("local");
  });
  it.each(["", "foo", "http://127.0.0.1:3000"])(
    "returns local env for arbitrary strings",
    () => {
      const result = getEnv("localhost:3000");
      expect(result).toEqual("local");
    },
  );
});

describe("formatDate", () => {
  it("formats ISO date string to en-GB long date and short time", () => {
    const dateStr = "2024-01-01T15:30:00Z";

    expect(formatDate(dateStr)).toBe("1 January 2024 at 15:30");
  });

  it("handles invalid date strings", () => {
    const dateStr = "not-a-date";

    expect(formatDate(dateStr)).toBe("Invalid Date");
  });
});

describe("formatTimeDelta", () => {
  it("returns correct text for zero and negative minutes", () => {
    expect(formatTimeDeltaText(0)).toEqual("a moment");
    expect(formatTimeDeltaText(-10)).toEqual("a moment");
  });

  it("returns correct text for minutes", () => {
    expect(formatTimeDeltaText(1)).toEqual("1 minute");
    expect(formatTimeDeltaText(2)).toEqual("2 minutes");
    expect(formatTimeDeltaText(10)).toEqual("10 minutes");
  });

  it("return correct text for less than hour", () => {
    expect(formatTimeDeltaText(30)).toEqual("less than an hour");
    expect(formatTimeDeltaText(40)).toEqual("less than an hour");
  });

  it("return correct text for hours", () => {
    expect(formatTimeDeltaText(60)).toEqual("1 hour");
    expect(formatTimeDeltaText(60 * 2)).toEqual("2 hours");
    expect(formatTimeDeltaText(60 * 2)).toEqual("2 hours");
  });

  it("return correct text for days", () => {
    expect(formatTimeDeltaText(60 * 24)).toEqual("1 day");
    expect(formatTimeDeltaText(60 * 24 * 2)).toEqual("2 days");
    expect(formatTimeDeltaText(60 * 24 * 3)).toEqual("3 days");
  });

  it("return correct text for months", () => {
    expect(formatTimeDeltaText(60 * 24 * 30)).toEqual("1 month");
    expect(formatTimeDeltaText(60 * 24 * 30 * 2)).toEqual("2 months");
    expect(formatTimeDeltaText(60 * 24 * 30 * 10)).toEqual("10 months");
  });

  it("return correct text for years", () => {
    expect(formatTimeDeltaText(60 * 24 * 30 * 12)).toEqual("1 year");
    expect(formatTimeDeltaText(60 * 24 * 30 * 12 * 2)).toEqual("2 years");
  });
});

describe("getTimeDeltaInMinutes", () => {
  it("calculates 1 minute ago", () => {
    const now = new Date();

    const MINUTE_IN_MILLISECONDS = 60 * 1000;
    const minuteDelta = getTimeDeltaInMinutes(
      now,
      new Date(now.getTime() - MINUTE_IN_MILLISECONDS),
    );
    expect(minuteDelta).toEqual(1);
  });

  it("calculates 1 year ago", () => {
    const now = new Date();

    const YEAR_IN_MILLISECONDS = 1000 * 60 * 24 * 30 * 12;
    const MINUTES_IN_YEAR = 24 * 30 * 12;
    const yearDalte = getTimeDeltaInMinutes(
      now,
      new Date(now.getTime() - YEAR_IN_MILLISECONDS),
    );
    expect(yearDalte).toEqual(MINUTES_IN_YEAR);
  });
});
