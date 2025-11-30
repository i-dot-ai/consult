import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";

import Header from "./Header.svelte";

describe("Header", () => {
  it("should render", () => {
    render(Header);
    expect(screen.getByRole("banner")).toBeInTheDocument();
    expect(screen.getByText("Consult")).toBeInTheDocument();
    expect(screen.getByText("Alpha")).toBeInTheDocument();
  });
});
