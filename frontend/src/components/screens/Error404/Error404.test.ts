import { describe, expect, it } from "vitest";
import { render, screen, waitFor } from "@testing-library/svelte";

import Error404 from "./Error404.svelte";

describe("EditUser", () => {
  it("should display error message if fetch fails", async () => {
    render(Error404);

    await waitFor(async () => {
      expect(screen.getByRole("heading", { name: "404 Not Found" })).toBeInTheDocument();
      expect(screen.getByText("The page you requested could not be found")).toBeInTheDocument();
    });
  });

  it("matches snapshot", () => {
    const { container } = render(Error404);
    expect(container).toMatchSnapshot();
  });
});
