import { describe, expect, it } from "vitest";

import { render, screen, waitFor } from "@testing-library/svelte";
import userEvent from "@testing-library/user-event";

import ManageConsultationsArchive from "./ManageConsultationsArchive.svelte";
import { CONSULTATIONS } from "./testData";

function parseCreatedAt(createdAtText: string) {
  const [dateStr, timeStr] = createdAtText.split(" at ");
  const [hourStr, minStr] = timeStr.split(":");
  const date = new Date(dateStr);

  const HOUR_IN_MILLISECONDS = 60 * 60 * 1000;
  const MIN_IN_MILLISECONDS = 60 * 1000;

  date.setTime(
    date.getTime() +
      parseInt(hourStr) * HOUR_IN_MILLISECONDS +
      parseInt(minStr) * MIN_IN_MILLISECONDS,
  );
  return date;
}

function buildCreatedAt(date: Date) {
  const year = date.getFullYear();
  const monthName = date.toLocaleString("default", { month: "long" });
  const day = date.getDate();
  const hour = date.getHours();
  const minute = date.getMinutes();
  return `${day} ${monthName} ${year} at ${hour}:${minute}`;
}

describe("ManageConsultationsArchive", () => {
  it.each(CONSULTATIONS)("should render consultation", async (consultation) => {
    render(ManageConsultationsArchive, { consultations: CONSULTATIONS });

    await waitFor(() => {
      expect(screen.getByText(consultation.title)).toBeInTheDocument();
    });

    const date = new Date(consultation.created_at);
    const createdAtText = buildCreatedAt(date);
    expect(screen.getAllByText(createdAtText).length).toBeGreaterThan(0);
  });

  it("should only show consultations matching search", async () => {
    render(ManageConsultationsArchive, { consultations: CONSULTATIONS });

    const user = userEvent.setup();
    await user.type(screen.getByLabelText("Search consultations"), "1");

    await waitFor(() => {
      const visibleConsultations = screen.getAllByTestId("consultation-item");
      expect(visibleConsultations).toHaveLength(1);
    });
  });

  it("should sort by descending if created at button is clicked", async () => {
    render(ManageConsultationsArchive, { consultations: CONSULTATIONS });

    const dateSortButton = screen.getByRole("button", {
      name: "sort consultations by Created At",
    });

    const user = userEvent.setup();
    await user.click(dateSortButton);

    const createdAtCells = screen.getAllByTestId("created-at");

    const timestamps = createdAtCells.map((el) => {
      const date = parseCreatedAt(el.textContent);
      return date.getTime();
    });

    const sortedTimestamps = [...timestamps].sort((a, b) => {
      if (a === b) {
        return 0;
      }
      return a > b ? 1 : -1;
    });

    expect(timestamps).toEqual(sortedTimestamps.reverse());
  });

  it("should sort by ascending/descending if name button is clicked", async () => {
    render(ManageConsultationsArchive, { consultations: CONSULTATIONS });

    const nameSortButton = screen.getByRole("button", {
      name: "sort consultations by Name",
    });

    const user = userEvent.setup();
    await user.click(nameSortButton);

    let createdAtCells = screen.getAllByTestId("title");
    let titles = createdAtCells.map((el) => el.textContent);

    const sortedTimestamps = [...titles].sort((a, b) => {
      if (a === b) {
        return 0;
      }
      return a < b ? -1 : 1;
    });

    await waitFor(() => {
      expect(titles).toEqual(sortedTimestamps);
    });

    await user.click(nameSortButton);

    await waitFor(() => {
      createdAtCells = screen.getAllByTestId("title");
      titles = createdAtCells.map((el) => el.textContent);
      expect(titles).toEqual(sortedTimestamps.reverse());
    });
  });

  it("should match snapshot initially", () => {
    const { container } = render(ManageConsultationsArchive, {
      consultations: CONSULTATIONS,
    });

    // Remove created at because pipeline timezone and local timezone
    // won't always be the same, causing snapshot conflict
    const allCreatedAtCells = screen.getAllByTestId("created-at");
    allCreatedAtCells.forEach((cell) => (cell.textContent = ""));

    expect(container).toMatchSnapshot();
  });
});
