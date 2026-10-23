import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/svelte";
import userEvent from "@testing-library/user-event";

import ChecksPage from "./ChecksPage.svelte";
import { CONSULTATION_ID } from "./mocks";

describe("ChecksPage", () => {
  const TEST_DATA = {
    consultationId: CONSULTATION_ID,
    dataSource: "qualtrics" as const,
  };

  it("renders the step title", () => {
    render(ChecksPage, TEST_DATA);

    expect(screen.getByText("Step 2 of 6")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { level: 1, name: "Prepare your file" }),
    ).toBeInTheDocument();
  });

  it("renders the structure section with provider-specific checks", () => {
    render(ChecksPage, TEST_DATA);

    expect(
      screen.getByText(/Rows 1 to 3 hold the question details/),
    ).toBeInTheDocument();
  });

  it("includes citizen-space row structure check for citizen-space data source", () => {
    render(ChecksPage, { ...TEST_DATA, dataSource: "citizen-space" as const });

    expect(
      screen.getByText(/Row 1 holds the question wording/),
    ).toBeInTheDocument();
  });

  it("uses 'From row 2' for citizen-space row structure", () => {
    render(ChecksPage, { ...TEST_DATA, dataSource: "citizen-space" as const });

    expect(
      screen.getByText(/From row 2, each row is one person/),
    ).toBeInTheDocument();
  });

  it("uses 'From row 4' for qualtrics row structure", () => {
    render(ChecksPage, TEST_DATA);

    expect(
      screen.getByText(/From row 4, each row is one person/),
    ).toBeInTheDocument();
  });

  it("renders both Structure and Content sections", () => {
    render(ChecksPage, TEST_DATA);

    expect(
      screen.getByRole("heading", { level: 2, name: "Structure" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { level: 2, name: "Content" }),
    ).toBeInTheDocument();
  });

  it("renders the technical checks section without checkboxes", () => {
    render(ChecksPage, TEST_DATA);

    expect(
      screen.getByText("Consult checks these when you upload"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("No need to check these yourself."),
    ).toBeInTheDocument();
  });

  it("shows Show example buttons for user checks", () => {
    render(ChecksPage, TEST_DATA);

    const showButtons = screen.getAllByRole("button", { name: "Show example" });
    expect(showButtons.length).toBeGreaterThan(0);
  });

  it("toggles example content on Show example click", async () => {
    render(ChecksPage, TEST_DATA);

    const showButton = screen.getAllByRole("button", {
      name: "Show example",
    })[0];
    await userEvent.click(showButton);

    expect(
      screen.getByRole("button", { name: "Hide example" }),
    ).toBeInTheDocument();
  });

  it("renders the Tick everything button", () => {
    render(ChecksPage, TEST_DATA);

    expect(
      screen.getByRole("button", { name: "Tick everything" }),
    ).toBeInTheDocument();
  });

  it("links back to the select provider page", () => {
    render(ChecksPage, TEST_DATA);

    expect(screen.getByRole("link", { name: "Back" })).toHaveAttribute(
      "href",
      `/consultations/${CONSULTATION_ID}/data-upload/select-provider`,
    );
  });

  it("continue button is always enabled", () => {
    render(ChecksPage, TEST_DATA);

    expect(
      screen.getByRole("link", { name: "Continue to upload" }),
    ).not.toBeDisabled();
  });

  it("links forward to the consultation page", () => {
    render(ChecksPage, TEST_DATA);

    expect(
      screen.getByRole("link", { name: "Continue to upload" }),
    ).toHaveAttribute("href", `/consultations/${CONSULTATION_ID}`);
  });

  it("matches snapshot", () => {
    const { container } = render(ChecksPage, TEST_DATA);
    expect(container).toMatchSnapshot();
  });
});
