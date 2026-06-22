import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";

import Error404 from "./Error404.svelte";

describe("Error404", () => {
  it("should display heading and text", async () => {
    render(Error404);

    expect(
      screen.getByRole("heading", { name: "404 Not Found" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("The page you requested could not be found"),
    ).toBeInTheDocument();
  });

  it("matches snapshot", () => {
    const { container } = render(Error404);
    expect(container).toMatchSnapshot();
  });
});
