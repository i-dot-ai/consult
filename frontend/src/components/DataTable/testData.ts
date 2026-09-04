export interface RowItem {
  id: number;
  name: string;
  createdAt: string;
}

export const ROWS = [
  {
    id: 1,
    name: "Test Item 1 - A",
    createdAt: "2026-08-19",
  },
  {
    id: 2,
    name: "Test Item 2 - B",
    createdAt: "2026-06-19",
  },
  {
    id: 3,
    name: "Test Item 3 - C",
    createdAt: "2025-10-10",
  },
];

export const COLUMNS = [
  {
    key: "name",
    label: "Name",
    sortable: true,
  },
  {
    key: "createdAt",
    label: "Date Created",
    sortable: true,

    sortValue: (item: RowItem) => new Date(item.createdAt).getTime(),
  },
];

export const COLUMN_SELECT = true;

export const SEARCHABLE = true;

export const extraColumns = [
  ...COLUMNS,
  {
    key: "column1",
    label: "Column One",
    sortable: true,
  },
  {
    key: "column2",
    label: "Column Two",
    sortable: true,
  },
  {
    key: "column3",
    label: "Column Three",
    sortable: true,
  },
  {
    key: "column4",
    label: "Column Four",
    sortable: true,
  },
  {
    key: "column5",
    label: "Column Five",
    sortable: true,
  },
  {
    key: "column6",
    label: "Column Six",
    sortable: true,
  },
];

export const extraRows = ROWS.map((row, i) => {
  return {
    ...row,
    column1: 10 * i,
    column2: 20 * i,
    column3: 30 * i,
    column4: 40 * i,
    column5: 50 * i,
    column6: 60 * i,
  };
});

export const CAPTION = "Example Data";

export const INITIAL_SORT = {
  key: "name",
  direction: "asc",
};

export const PAGE_SIZES = [10, 100, 1000];

export const LOADING = false;

export const SORTABLE = true;

export const PAGINATED = true;

export const SEARCH_PLACEHOLDER = "";

export const onRowClick = (row: RowItem) => alert("Row clicked: " + row.name);

export const TEST_DATA = {
  rows: ROWS,
  columns: COLUMNS,
  caption: CAPTION,
  initialSort: INITIAL_SORT,
  pageSizes: PAGE_SIZES,
  loadingCondition: LOADING,
  columnSelect: COLUMN_SELECT,
  searchable: SEARCHABLE,
  searchPlaceholder: SEARCH_PLACEHOLDER,
  sortable: SORTABLE,
  paginated: PAGINATED,
  onRowClick,
};
