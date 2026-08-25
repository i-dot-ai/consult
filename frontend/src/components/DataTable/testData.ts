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

export const CAPTION = "Example Data";

export const INITIAL_SORT = {
  key: "name",
  direction: "asc",
};

export const LOADING = false;

export const onRowClick = (row: RowItem) => alert("Row clicked: " + row.name);

export const TEST_DATA = {
  rows: ROWS,
  columns: COLUMNS,
  caption: CAPTION,
  initialSort: INITIAL_SORT,
  loading: LOADING,
  onRowClick,
};
