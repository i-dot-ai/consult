import { afterEach, beforeEach, describe, expect, it, test, vi } from "vitest";
import { applyHighlight, getEnv, getPercentage, toTitleCase } from "./utils";

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
