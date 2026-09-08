import { describe, expect, it } from "vitest";

import { render, screen, waitFor } from "@testing-library/svelte";

import ManageConsultationsArchive, {
  buildDateTimeString,
} from "./ManageConsultationsArchive.svelte";
import { CONSULTATIONS } from "./testData";

describe("ManageConsultationsArchive", () => {
  it.each(CONSULTATIONS)("should render consultation", async (consultation) => {
    render(ManageConsultationsArchive, { consultations: CONSULTATIONS });

    await waitFor(() => {
      expect(screen.getByText(consultation.title)).toBeInTheDocument();
    });

    const date = new Date(consultation.created_at);
    const createdAtText = buildDateTimeString(date);
    expect(screen.getAllByText(createdAtText).length).toBeGreaterThan(0);
  });

  it("should match snapshot initially", () => {
    const { container } = render(ManageConsultationsArchive, {
      consultations: CONSULTATIONS,
    });

    // Remove created at because pipeline timezone and local timezone
    // won't always be the same, causing snapshot conflict
    const allCreatedAtCells = screen.getAllByTestId("cell-createdAt");
    allCreatedAtCells.forEach((cell) => (cell.textContent = ""));

    expect(container).toMatchSnapshot();
  });
});
