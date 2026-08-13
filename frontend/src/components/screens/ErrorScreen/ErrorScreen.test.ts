import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";

import ErrorScreen from "./ErrorScreen.svelte";

describe("ErrorScreen", () => {
  it("should display heading and text for status 404", async () => {
    render(ErrorScreen);

    expect(
      screen.getByRole("heading", { name: "404 Not Found" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("The page you requested could not be found"),
    ).toBeInTheDocument();
  });

  it("should display heading and text for status 500", async () => {
    render(ErrorScreen, { status: 500 });

    expect(
      screen.getByRole("heading", { name: "500 Internal Server Error" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
  });

  it("matches snapshot 404", () => {
    const { container } = render(ErrorScreen);
    expect(container).toMatchSnapshot();
  });

  it("matches snapshot 500", () => {
    const { container } = render(ErrorScreen, { status: 500 });
    expect(container).toMatchSnapshot();
  });
});
