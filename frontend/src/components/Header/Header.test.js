import { describe, expect, it } from "vitest";
import { render } from "@testing-library/svelte";

import Header from "./Header.svelte";
import HeaderStory from "./HeaderStory.svelte";

describe("Header", () => {
  it("should render", () => {
    const { container, getByText } = render(Header);
    expect(container.querySelector("header")).toBeTruthy();
    expect(getByText("Consult"));
    expect(getByText("Alpha"));
  });

  it("should render story", () => {
    render(HeaderStory);
  });
});
