import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";

import Header from "./Header.svelte";

describe("Header", () => {
  it("should render", () => {
    const { container } = render(Header);
    expect(container.querySelector("header")).toBeTruthy();
    expect(screen.getByText("Consult")).toBeInTheDocument();
    expect(screen.getByText("Alpha")).toBeInTheDocument();
  });
});
