import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";

import SectionTest from "./SectionTest.svelte";

describe("Section", () => {
  it("should render", () => {
    render(SectionTest);
    expect(screen.getByText("Test Slot")).toBeInTheDocument();
  });
});
