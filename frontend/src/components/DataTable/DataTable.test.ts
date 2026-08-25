import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/svelte";
import userEvent from "@testing-library/user-event";

import DataTable from "./DataTable.svelte";
import {
  CAPTION,
  COLUMNS,
  INITIAL_SORT,
  LOADING,
  onRowClick,
  ROWS,
} from "./testData";

describe("DataTable", () => {
  const TEST_DATA = {
    caption: CAPTION,
    columns: COLUMNS,
    rows: ROWS,
    loading: LOADING,
    initialSort: INITIAL_SORT,
    onRowClick: onRowClick,
  };

  it.each(TEST_DATA.columns)("should render column label", (column) => {
    render(DataTable, TEST_DATA as Record<string, unknown>);

    expect(screen.getByText(column.label)).toBeInTheDocument();
  });

  it.each(TEST_DATA.rows)("should render row data", (row) => {
    render(DataTable, TEST_DATA as Record<string, unknown>);

    expect(screen.getByText(row.name)).toBeInTheDocument();
    expect(screen.getByText(row.createdAt)).toBeInTheDocument();
  });

  it("should call callback when a row is clicked", async () => {
    const onRowClickCallback = vi.fn();
    render(DataTable, {
      ...TEST_DATA,
      onRowClick: onRowClickCallback,
    } as Record<string, unknown>);

    const firstRow = ROWS[0];
    const rowElement = screen.getByText(firstRow.name);
    const user = userEvent.setup();
    await user.click(rowElement);

    expect(onRowClickCallback).toHaveBeenCalledWith({
      createdAt: "2026-08-19",
      id: 1,
      name: "Test Item 1 - A",
    });
  });

  it("should display correct default page size options", async () => {
    const PAGE_SIZES = [10, 50, 100, 250, 500];

    render(DataTable, TEST_DATA as Record<string, unknown>);

    const pageSizeSelectOptions = screen.getAllByTestId(
      "page-size-select-option",
    );

    expect(pageSizeSelectOptions).toHaveLength(5);

    for (let i = 0; i < PAGE_SIZES.length; i++) {
      expect(pageSizeSelectOptions[i]).toHaveTextContent(
        PAGE_SIZES[i].toString(),
      );
    }
  });

  it("should display paginate items", async () => {
    const PAGE_SIZES = [1, 3];

    render(DataTable, {
      ...TEST_DATA,
      pageSizes: PAGE_SIZES,
    } as Record<string, unknown>);

    const lastRow = ROWS[ROWS.length - 1];
    expect(screen.queryByText(lastRow.name)).not.toBeInTheDocument();
    expect(screen.getByTestId("visible-items-text")).toHaveTextContent("Showing 1 - 1 of 3");

    const pageSizeSelect = screen.getByRole("combobox");

    const user = userEvent.setup();
    await user.selectOptions(pageSizeSelect, "3");

    expect(screen.getByText(lastRow.name)).toBeInTheDocument();
    expect(screen.getByTestId("visible-items-text")).toHaveTextContent("Showing 1 - 3 of 3");
  });

  it("should change items displayed when navinagated to other pages", async () => {
    const PAGE_SIZES = [1];

    render(DataTable, {
      ...TEST_DATA,
      pageSizes: PAGE_SIZES,
    } as Record<string, unknown>);

    let currentPage = 1;
    const user = userEvent.setup();
    const nextButton = screen.getByLabelText("Next Page");
    const prevButton = screen.getByLabelText("Previous Page");

    const assertVisibleItems = (currentPage: number) => {
      for (let i=0; i<ROWS.length; i++) {
        if (i === currentPage - 1) {
          expect(screen.getByText(ROWS[i].name)).toBeInTheDocument();
        } else {
          expect(screen.queryByText(ROWS[i].name)).not.toBeInTheDocument();
        }
      }
      expect(screen.getByTestId("visible-items-text")).toHaveTextContent(`Showing ${currentPage} - ${currentPage} of ${ROWS.length}`);
      expect(screen.getByTestId("current-page")).toHaveTextContent(`Page ${currentPage} of ${ROWS.length}`);
    }

    const goNext = async () => {
      await user.click(nextButton);
      currentPage += 1;
    }

    const goPrev = async () => {
      await user.click(prevButton);
      currentPage -= 1;
    }

    assertVisibleItems(currentPage);

    await goNext();
    assertVisibleItems(currentPage);

    await goNext();
    assertVisibleItems(currentPage);

    await goPrev();
    assertVisibleItems(currentPage);

    await goPrev();
    assertVisibleItems(currentPage);
  });

  it("should disable prev button if on first page", async () => {
    render(DataTable, TEST_DATA as Record<string, unknown>);

    const nextButton = screen.getByLabelText("Next Page");
    expect(nextButton).toBeDisabled();
  });

  it("should display correct custom page size options", async () => {
    const PAGE_SIZES = [1, 5, 15, 30];

    render(DataTable, {
      ...TEST_DATA,
      pageSizes: PAGE_SIZES,
    } as Record<string, unknown>);

    const pageSizeSelectOptions = screen.getAllByTestId(
      "page-size-select-option",
    );

    expect(pageSizeSelectOptions).toHaveLength(4);

    for (let i = 0; i < PAGE_SIZES.length; i++) {
      expect(pageSizeSelectOptions[i]).toHaveTextContent(
        PAGE_SIZES[i].toString(),
      );
    }
  });

  it("should initially show 10 items", () => {
    render(DataTable, TEST_DATA as Record<string, unknown>);

    const pageSizeSelect = screen.getByRole("combobox");

    expect(pageSizeSelect).toHaveValue("10");
  });

  it("should match snapshot", () => {
    const { container } = render(
      DataTable,
      TEST_DATA as Record<string, unknown>,
    );
    expect(container).toMatchSnapshot();
  });
});
