import { describe, expect, it, test } from "vitest";
import { render } from "@testing-library/svelte";

import Footer from "./Footer.svelte";
import FooterStory from "./FooterStory.svelte";

describe("Footer", () => {
  it("should render", () => {
    const { container, getByTestId } = render(Footer);
    expect(container.querySelector("footer")).toBeTruthy();
    expect(getByTestId("privacy-link").href).toContain("/privacy/");
  });

  it("should render story", () => {
    render(FooterStory);
  });
});
