import { describe, expect, it } from "vitest";

import { getAddedNotice, getPeopleCountText } from "./people";

describe("getAddedNotice", () => {
  it("counts the people added", () => {
    expect(getAddedNotice(0, [])).toBe("Nobody added.");
    expect(getAddedNotice(1, [])).toBe("1 person added.");
    expect(getAddedNotice(2, [])).toBe("2 people added.");
  });

  it("names the addresses already on the consultation", () => {
    expect(getAddedNotice(1, ["a@example.gov.uk"])).toBe(
      "1 person added. a@example.gov.uk is already on this consultation.",
    );
    expect(getAddedNotice(0, ["a@example.gov.uk", "b@example.gov.uk"])).toBe(
      "Nobody added. a@example.gov.uk, b@example.gov.uk are already on this consultation.",
    );
  });

  it("names at most three addresses and counts the rest", () => {
    const emails = ["a", "b", "c", "d", "e"].map(
      (letter) => `${letter}@example.gov.uk`,
    );
    expect(getAddedNotice(1, emails)).toBe(
      "1 person added. a@example.gov.uk, b@example.gov.uk, c@example.gov.uk and 2 others are already on this consultation.",
    );
    expect(getAddedNotice(1, emails.slice(0, 4))).toContain("and 1 other are");
  });
});

describe("getPeopleCountText", () => {
  it("pluralises people", () => {
    expect(getPeopleCountText(1)).toBe("1 person");
    expect(getPeopleCountText(14)).toBe("14 people");
  });
});
