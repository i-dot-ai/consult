import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";

import Finalisation from "./Finalisation.svelte";
import { CONSULTATION_ID } from "./mocks";

describe("Finalisation", () => {
  const TEST_DATA = {
    consultationId: CONSULTATION_ID,
  };

  it("renders the step title", () => {
    render(Finalisation, TEST_DATA);

    expect(screen.getByText("Step 6 of 6")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { level: 1, name: "Setup complete" }),
    ).toBeInTheDocument();
  });

  it("links to the consultation page", () => {
    render(Finalisation, TEST_DATA);

    expect(
      screen.getByRole("link", { name: "Go to consultation page" }),
    ).toHaveAttribute("href", `/consultations/${CONSULTATION_ID}`);
  });

  it("matches snapshot", () => {
    const { container } = render(Finalisation, TEST_DATA);
    expect(container).toMatchSnapshot();
  });
});
