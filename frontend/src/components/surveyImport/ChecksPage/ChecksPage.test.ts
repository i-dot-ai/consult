import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";

import ChecksPage from "./ChecksPage.svelte";
import { CONSULTATION_ID } from "./mocks";

describe("ChecksPage", () => {
  const TEST_DATA = {
    consultationId: CONSULTATION_ID,
    dataSource: "qualtrics" as const,
  };

  it("renders the step title", () => {
    render(ChecksPage, TEST_DATA);

    expect(screen.getByText("Step 3 of 6")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { level: 1, name: "Check your data" }),
    ).toBeInTheDocument();
  });

  it("renders the user checks section", () => {
    render(ChecksPage, TEST_DATA);

    expect(screen.getByText("User checks")).toBeInTheDocument();
  });

  it("includes provider-specific checks within the user checks section", () => {
    render(ChecksPage, TEST_DATA);

    expect(
      screen.getByText(/Rows 1–3 contain question and metadata headers/),
    ).toBeInTheDocument();
  });

  it("includes citizen-space row structure check for citizen-space data source", () => {
    render(ChecksPage, { ...TEST_DATA, dataSource: "citizen-space" as const });

    expect(
      screen.getByText(/Row 1 contains question text, row 2 onwards/),
    ).toBeInTheDocument();
  });

  it("renders the technical checks section", () => {
    render(ChecksPage, TEST_DATA);

    expect(screen.getByText("Technical checks")).toBeInTheDocument();
  });

  it("links back to the select provider page", () => {
    render(ChecksPage, TEST_DATA);

    expect(screen.getByRole("link", { name: "Back" })).toHaveAttribute(
      "href",
      `/consultations/${CONSULTATION_ID}/data-upload/select-provider`,
    );
  });

  it("has the continue button disabled when no boxes are checked", () => {
    render(ChecksPage, TEST_DATA);

    expect(
      screen.getByRole("button", { name: "Continue to upload" }),
    ).toBeDisabled();
  });

  it("links forward to the consultation page when all boxes are checked", async () => {
    render(ChecksPage, TEST_DATA);

    const checkboxes = screen.getAllByRole("checkbox");
    for (const checkbox of checkboxes) {
      await checkbox.click();
    }

    expect(
      screen.getByRole("link", { name: "Continue to upload" }),
    ).toHaveAttribute("href", `/consultations/${CONSULTATION_ID}`);
  });

  it("matches snapshot", () => {
    const { container } = render(ChecksPage, TEST_DATA);
    expect(container).toMatchSnapshot();
  });
});
