import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";

import Footer from "./Footer.svelte";

describe("Footer", () => {
  it("should render", () => {
    const { container } = render(Footer);
    expect(container.querySelector("footer")).toBeTruthy();
    expect(screen.getByTestId("privacy-link").href).toContain("/privacy/");
  });
});
