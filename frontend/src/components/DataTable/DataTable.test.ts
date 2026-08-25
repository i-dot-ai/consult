import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/svelte";
import userEvent from "@testing-library/user-event";

import DataTable from "./DataTable.svelte";
import { TEST_DATA } from "./testData";

describe("DataTable", () => {
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

    const firstRow = TEST_DATA.rows[0];
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

  it("should update visible items when page size is changed", async () => {
    const PAGE_SIZES = [1, 3];

    render(DataTable, {
      ...TEST_DATA,
      pageSizes: PAGE_SIZES,
    } as Record<string, unknown>);

    const lastRow = TEST_DATA.rows[TEST_DATA.rows.length - 1];
    expect(screen.queryByText(lastRow.name)).not.toBeInTheDocument();
    expect(screen.getByTestId("visible-items-text")).toHaveTextContent(
      "Showing 1 - 1 of 3",
    );

    const pageSizeSelect = screen.getByRole("combobox");

    const user = userEvent.setup();
    await user.selectOptions(pageSizeSelect, "3");

    expect(screen.getByText(lastRow.name)).toBeInTheDocument();
    expect(screen.getByTestId("visible-items-text")).toHaveTextContent(
      "Showing 1 - 3 of 3",
    );
  });

  it("should set current page to first page when a different page size is selected", async () => {
    const PAGE_SIZES = [1, 3];

    render(DataTable, {
      ...TEST_DATA,
      pageSizes: PAGE_SIZES,
    } as Record<string, unknown>);

    const pageSizeSelect = screen.getByRole("combobox");
    const nextButton = screen.getByLabelText("Next Page");
    const user = userEvent.setup();

    // go to page 2
    await user.click(nextButton);

    // only second is visible with page size 1
    expect(screen.queryByText(TEST_DATA.rows[0].name)).not.toBeInTheDocument();
    expect(screen.getByText(TEST_DATA.rows[1].name)).toBeInTheDocument();
    expect(screen.queryByText(TEST_DATA.rows[2].name)).not.toBeInTheDocument();

    // change page size to 3
    await user.selectOptions(pageSizeSelect, "3");

    // all are visible because page size is 3 and current page is set to 1
    for (const row of TEST_DATA.rows) {
      expect(screen.getByText(row.name)).toBeInTheDocument();
    }
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
      for (let pageIndex = 0; pageIndex < TEST_DATA.rows.length; pageIndex++) {
        if (pageIndex === currentPage - 1) {
          // eslint-disable-next-line vitest/no-conditional-expect
          expect(screen.getByText(TEST_DATA.rows[pageIndex].name)).toBeInTheDocument();
        } else {
          // eslint-disable-next-line vitest/no-conditional-expect
          expect(
            screen.queryByText(TEST_DATA.rows[pageIndex].name),
          ).not.toBeInTheDocument();
        }
      }
      expect(screen.getByTestId("visible-items-text")).toHaveTextContent(
        `Showing ${currentPage} - ${currentPage} of ${TEST_DATA.rows.length}`,
      );
      expect(screen.getByTestId("current-page")).toHaveTextContent(
        `Page ${currentPage} of ${TEST_DATA.rows.length}`,
      );
    };

    const goNext = async () => {
      await user.click(nextButton);
      currentPage += 1;
    };

    const goPrev = async () => {
      await user.click(prevButton);
      currentPage -= 1;
    };

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

  it("should display loading indicator if loading", async () => {
    render(DataTable, {
      ...TEST_DATA,
      loading: true,
    } as Record<string, unknown>);

    expect(screen.getByTestId("loading-indicator")).toBeInTheDocument();
  });

  it("should display no data message if no data and not loading", async () => {
    render(DataTable, {
      ...TEST_DATA,
      loading: false,
      rows: [],
    } as Record<string, unknown>);

    expect(screen.getByText("No data available")).toBeInTheDocument();
  });

  it("should match snapshot", () => {
    const { container } = render(
      DataTable,
      TEST_DATA as Record<string, unknown>,
    );
    expect(container).toMatchSnapshot();
  });
});
