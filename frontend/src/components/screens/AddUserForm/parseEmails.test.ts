import { describe, expect, it } from "vitest";

import { parseEmails } from "./parseEmails";

describe("parseEmails", () => {
  it("handles commas, spaces, and newlines when parsing a list of emails from a string", () => {
    const input =
      "test1@example.com,test2@example.com test3@example.com\ntext4@example.com     \n\n,   test5@example.com  ";
    const expected = [
      "test1@example.com",
      "test2@example.com",
      "test3@example.com",
      "text4@example.com",
      "test5@example.com",
    ];

    expect(parseEmails(input)).toEqual(expected);
  });
});
