import { describe, expect, it } from "vitest";

import { render, screen, waitFor } from "@testing-library/svelte";
import userEvent from "@testing-library/user-event";

import ManageConsultationsArchive from "./ManageConsultationsArchive.svelte";
import { CONSULTATIONS } from "./testData";

function parseCreatedAt(createdAtText: string) {
  const [dateStr, timeStr] = createdAtText.split(" at ");
  const [hourStr, minStr] = timeStr.split(":");
  const date = new Date(dateStr);
  
  date.setTime(date.getTime() + parseInt(hourStr)*60*60*1000 + parseInt(minStr)*60*1000);
  return date;
}

function buildCreatedAt(date: Date) {
  const year = date.getFullYear();
  const monthName = date.toLocaleString('default', { month: 'long' });
  const day = date.getDate();
  const hour = date.getHours();
  const minute = date.getMinutes();
  return `${day} ${monthName} ${year} at ${hour}:${minute}`;
}

describe("ManageConsultationsArchive", () => {
  it.each(CONSULTATIONS)("should render consultation", async (consultation) => {
    render(ManageConsultationsArchive, { consultations: CONSULTATIONS });

    await waitFor(() => {
      expect(
        screen.getByText(consultation.title),
      ).toBeInTheDocument();
    });

    const date = new Date(consultation.created_at);
    const createdAtText = buildCreatedAt(date);
    expect(screen.getAllByText(createdAtText).length).toBeGreaterThan(0);
  });

  it("should sort by descending if created at button is clicked", async () => {
    render(ManageConsultationsArchive, { consultations: CONSULTATIONS });

    const user = userEvent.setup();
    await user.type(screen.getByLabelText("Search consultations"), "1");

    const visibleConsultations = screen.getAllByTestId("consultation-item");
    await waitFor(() => {
      expect(visibleConsultations).toHaveLength(1);
    })
  });

  it("should sort by descending if created at button is clicked", async () => {
    render(ManageConsultationsArchive, { consultations: CONSULTATIONS });

    const dateSortButton = screen.getByRole("button", { name: "sort consultations by Created At" });

    const user = userEvent.setup();
    await user.click(dateSortButton);

    const createdAtCells = screen.getAllByTestId("created-at");

    const timestamps = createdAtCells.map(el => {
      const date = parseCreatedAt(el.textContent);
      return date.getTime();
    })

    const sortedTimestamps = [...timestamps].sort((a,b) => b - a);

    expect(timestamps).toEqual(sortedTimestamps.reverse());
  });

  it("should sort by ascending/descending if name button is clicked", async () => {
    render(ManageConsultationsArchive, { consultations: CONSULTATIONS });

    const nameSortButton = screen.getByRole("button", { name: "sort consultations by Name" });

    const user = userEvent.setup();
    await user.click(nameSortButton);

    const createdAtCells = screen.getAllByTestId("title");

    const titles = createdAtCells.map(el => el.textContent)

    const sortedTimestamps = [...titles].sort((a,b) => {
      if (a === b) {
        return 0;
      }
      return a < b ? -1 : 1;
    });

    await waitFor(() => {
      expect(titles).toEqual(sortedTimestamps);
    })

    await user.click(nameSortButton);

    await waitFor(() => {
      expect(titles).toEqual(sortedTimestamps.reverse());
    })
  });

  it("should match snapshot initially", () => {
    const { container } = render(ManageConsultationsArchive, {
      consultations: CONSULTATIONS,
    });
    expect(container).toMatchSnapshot();
  });
});
