import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";

import Footer from "./Footer.svelte";

describe("Footer", () => {
  it("should render", () => {
    render(Footer);
    expect(screen.getByRole("contentinfo")).toBeInTheDocument();
    expect(
      (screen.getByTestId("privacy-link") as HTMLAnchorElement).href,
    ).toContain("/privacy/");
  });
});
