import { describe, expect, it } from "vitest";
import { render } from "@testing-library/svelte";

import Header from "./Header.svelte";

describe("Header", () => {
  it("should render", () => {
    const { container, getByText } = render(Header);
    expect(container.querySelector("header")).toBeTruthy();
    expect(getByText("Consult"));
    expect(getByText("Alpha"));
  });
});
