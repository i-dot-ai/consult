import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/svelte";
import userEvent from "@testing-library/user-event";

import DataTable from "./DataTable.svelte";
import { TEST_DATA } from "./testData";

function isRowsSorted(rows: HTMLElement[], reverse?: boolean) {
  for (let i = 0; i < rows.length - 1; i++) {
    const contentA = rows[i].textContent;
    const contentB = rows[i + 1].textContent;

    if (contentA > contentB && !reverse) {
      return false;
    }
    if (contentB > contentA && reverse) {
      return false;
    }
  }
  return true;
}

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
    render(DataTable, TEST_DATA as Record<string, unknown>);

    const pageSizeSelectOptions = screen.getAllByTestId(
      "page-size-select-option",
    );

    expect(pageSizeSelectOptions).toHaveLength(TEST_DATA.pageSizes.length);

    for (let i = 0; i < TEST_DATA.pageSizes.length; i++) {
      expect(pageSizeSelectOptions[i]).toHaveTextContent(
        TEST_DATA.pageSizes[i].toString(),
      );
    }
  });

  it("should display correct custom page size options", async () => {
    const CUSTOM_PAGE_SIZES = [10, 50, 100, 250, 500];

    render(DataTable, {
      ...TEST_DATA,
      pageSizes: CUSTOM_PAGE_SIZES,
    } as Record<string, unknown>);

    const pageSizeSelectOptions = screen.getAllByTestId(
      "page-size-select-option",
    );

    expect(pageSizeSelectOptions).toHaveLength(CUSTOM_PAGE_SIZES.length);

    for (let i = 0; i < CUSTOM_PAGE_SIZES.length; i++) {
      expect(pageSizeSelectOptions[i]).toHaveTextContent(
        CUSTOM_PAGE_SIZES[i].toString(),
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

    const pageSizeSelect = screen.getByLabelText("Page Size");

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

    const pageSizeSelect = screen.getByLabelText("Page Size");
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

  it("should display page related elements if paginated", () => {
    render(DataTable, {
      ...TEST_DATA,
      paginated: true,
    } as Record<string, unknown>);

    expect(screen.getByTestId("current-page")).toBeInTheDocument();
    expect(screen.getByLabelText("Page Size")).toBeInTheDocument();
    expect(screen.getByTestId("visible-items-text")).toBeInTheDocument();
    expect(screen.getByLabelText("Previous Page")).toBeInTheDocument();
    expect(screen.getByLabelText("Next Page")).toBeInTheDocument();
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
          expect(
            screen.getByText(TEST_DATA.rows[pageIndex].name),
          ).toBeInTheDocument();
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

    const prevButton = screen.getByLabelText("Previous Page");
    expect(prevButton).toBeDisabled();
  });

  it("should disable next button if on last page", async () => {
    render(DataTable, {
      ...TEST_DATA,
      pageSizes: [1],
    } as Record<string, unknown>);

    const nextButton = screen.getByLabelText("Next Page");
    const user = userEvent.setup();

    // navigate to last page
    for (let i = 0; i < TEST_DATA.rows.length - 1; i++) {
      await user.click(nextButton);
    }

    // now on last page, next should be disabled
    expect(nextButton).toBeDisabled();
  });

  it("should initially show 10 items", () => {
    render(DataTable, TEST_DATA as Record<string, unknown>);

    const pageSizeSelect = screen.getByLabelText("Page Size");

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

  it("should clear search query if reset search button is clicked", async () => {
    render(DataTable, TEST_DATA as Record<string, unknown>);

    const user = userEvent.setup();

    const searchInput = screen.getByLabelText("Search");
    await user.type(searchInput, "text that does not exist in the data");
    expect(screen.getByText("No data available")).toBeInTheDocument();

    const searchResetButton = screen.getByLabelText("Reset search");
    await user.click(searchResetButton);
    expect(screen.queryByText("No data available")).not.toBeInTheDocument();
  });

  it("should display items found as a result of search query", async () => {
    render(DataTable, TEST_DATA as Record<string, unknown>);

    const user = userEvent.setup();

    const searchInput = screen.getByLabelText("Search");
    await user.type(searchInput, TEST_DATA.rows[0].name);

    expect(screen.getByText(TEST_DATA.rows[0].name)).toBeInTheDocument();
    expect(screen.queryByText(TEST_DATA.rows[1].name)).not.toBeInTheDocument();
    expect(screen.queryByText(TEST_DATA.rows[2].name)).not.toBeInTheDocument();
    expect(screen.queryByText("No data available")).not.toBeInTheDocument();
  });

  it("should display nothing if search query does not match anything", async () => {
    render(DataTable, TEST_DATA as Record<string, unknown>);

    const user = userEvent.setup();

    const searchInput = screen.getByLabelText("Search");
    await user.type(searchInput, "some text that will not match");

    expect(screen.queryByText(TEST_DATA.rows[0].name)).not.toBeInTheDocument();
    expect(screen.queryByText(TEST_DATA.rows[1].name)).not.toBeInTheDocument();
    expect(screen.queryByText(TEST_DATA.rows[2].name)).not.toBeInTheDocument();
    expect(screen.getByText("No data available")).toBeInTheDocument();
  });

  it("should switch between ascending and descending sort when columns are clicked", async () => {
    render(DataTable, {
      ...TEST_DATA,
      initialSort: undefined,
    } as Record<string, unknown>);

    let rows;
    const user = userEvent.setup();
    const sortButton = screen.getByLabelText("Sort by Name");

    await user.click(sortButton);
    rows = screen.getAllByTestId("datatable-row");
    expect(isRowsSorted(rows)).toBeTruthy();

    await user.click(sortButton);
    rows = screen.getAllByTestId("datatable-row");
    expect(isRowsSorted(rows, true)).toBeTruthy();
  });

  it("should call sort callback when a sort button is clicked", async () => {
    const onSortChangeCallback = vi.fn();

    render(DataTable, {
      ...TEST_DATA,
      onSortChange: onSortChangeCallback,
    } as Record<string, unknown>);

    const user = userEvent.setup();
    const sortButton = screen.getByLabelText("Sort by Date Created");

    await user.click(sortButton);

    expect(onSortChangeCallback).toHaveBeenCalledWith({
      key: "createdAt",
      direction: "asc",
    });
  });

  it("should render custom searchPlaceholder", async () => {
    const SEARCH_PLACEHOLDER = "Test Placeholder";

    render(DataTable, {
      ...TEST_DATA,
      searchPlaceholder: SEARCH_PLACEHOLDER,
    } as Record<string, unknown>);

    const searchInput = screen.getByLabelText("Search");
    expect(searchInput).toHaveAttribute("placeholder", SEARCH_PLACEHOLDER);
  });

  it("should display correct labels for sort buttons depending on sort applied", async () => {
    render(DataTable, {
      ...TEST_DATA,
      initialSort: undefined,
    } as Record<string, unknown>);

    const user = userEvent.setup();
    const sortButton = screen.getByLabelText("Sort by Name");

    await user.click(sortButton);
    expect(sortButton).toHaveAttribute(
      "aria-label",
      "Sorted ascending by Name. Click to sort descending.",
    );

    await user.click(sortButton);
    expect(sortButton).toHaveAttribute(
      "aria-label",
      "Sorted descending by Name. Click to sort ascending.",
    );
  });

  it("should not render column select if not columnSelect enabled", async () => {
    render(DataTable, {
      ...TEST_DATA,
      columnSelect: false,
    } as Record<string, unknown>);

    expect(screen.queryByLabelText("Visible columns")).not.toBeInTheDocument();
  });

  it("should not render search input if not searchable", async () => {
    render(DataTable, {
      ...TEST_DATA,
      searchable: false,
    } as Record<string, unknown>);

    expect(screen.queryByLabelText("Search")).not.toBeInTheDocument();
  });

  it("should not paginate if not paginated", async () => {
    render(DataTable, {
      ...TEST_DATA,
      paginated: false,
      pageSizes: [1],
    } as Record<string, unknown>);

    for (let i = 0; i < TEST_DATA.rows.length; i++) {
      expect(screen.getByText(TEST_DATA.rows[i].name)).toBeInTheDocument();
    }

    // Assert that page related elements are hidden
    expect(screen.queryByTestId("current-page")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Page Size")).not.toBeInTheDocument();
    expect(screen.queryByTestId("visible-items-text")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Previous Page")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Next Page")).not.toBeInTheDocument();
  });

  it("should toggle visibility of columns via column select", async () => {
    render(DataTable, TEST_DATA as Record<string, unknown>);

    const user = userEvent.setup();
    const columnSelect = screen.getByLabelText("Visible columns");

    const numExpectedColumnOptions = TEST_DATA.columns.length;
    const numExpectedVisibleColumnsBefore = TEST_DATA.columns.length;
    const numExpectedVisibleColumnsAfter = TEST_DATA.columns.length - 1;

    // expect all columns to be visible initially
    expect(screen.getAllByTestId("column-header")).toHaveLength(
      numExpectedVisibleColumnsBefore,
    );

    // click reveals options
    await user.click(columnSelect);

    // there's an option for each column
    const columnOptions = screen.getAllByTestId("searchable-select-option");
    expect(columnOptions).toHaveLength(numExpectedColumnOptions);

    // click on first option in the dropdown
    const firstColumnOption = columnOptions.at(0);
    await user.click(firstColumnOption!);

    // expect one column to be hidden at this point
    expect(screen.getAllByTestId("column-header")).toHaveLength(
      numExpectedVisibleColumnsAfter,
    );

    // click select again to reveal dropdown, it's disappeared after last click
    await user.click(columnSelect);

    // click on the first option again to reveal it back
    await user.click(screen.getAllByTestId("searchable-select-option").at(0)!);

    // expect that all columns are visible again
    expect(screen.getAllByTestId("column-header")).toHaveLength(
      numExpectedVisibleColumnsBefore,
    );
  });

  it("should not render column headers as sort buttons if not sortable", async () => {
    render(DataTable, {
      ...TEST_DATA,
      sortable: false,
    } as Record<string, unknown>);

    for (const columnName of TEST_DATA.columns.map((col) => col.label)) {
      expect(
        screen.queryAllByLabelText(
          `Sorted ascending by ${columnName}. Click to sort descending.`,
        ),
      ).toHaveLength(0);
      expect(
        screen.queryAllByLabelText(
          `Sorted descending by ${columnName}. Click to sort ascending.`,
        ),
      ).toHaveLength(0);
      expect(screen.queryAllByLabelText(`Sort by ${columnName}`)).toHaveLength(
        0,
      );
    }
  });

  it("should apply initial sort", async () => {
    render(DataTable, {
      ...TEST_DATA,
      initialSort: {
        key: "createdAt",
        direction: "desc",
      },
    } as Record<string, unknown>);

    // custom initial sort should be applied
    expect(
      screen.getByLabelText(
        "Sorted descending by Date Created. Click to sort ascending.",
      ),
    ).toBeInTheDocument();
    // default initial sort should not be applied
    expect(
      screen.queryByLabelText(
        "Sorted ascending by Name. Click to sort descending.",
      ),
    ).not.toBeInTheDocument();
  });

  it("should match snapshot", () => {
    const { container } = render(
      DataTable,
      TEST_DATA as Record<string, unknown>,
    );

    expect(container).toMatchSnapshot();
  });
});
