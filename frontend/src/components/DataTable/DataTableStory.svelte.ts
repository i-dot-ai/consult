import DataTable from "./DataTable.svelte";

interface RowItem {
  id: number;
  name: string;
  createdAt: string;
}

const rows = $state([
  {
    id: 1,
    name: "Test Item 1",
    createdAt: "2026-08-19",
  },
  {
    id: 2,
    name: "Test Item 2",
    createdAt: "2026-06-19",
  },
  {
    id: 3,
    name: "Test Item 3",
    createdAt: "2025-10-10",
  },
]);

const columns = $state([
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
]);

const caption = $state("Example Data");

const initialSort = $state({
  key: "name",
  direction: "asc",
});

const loading = $state(false);

const onRowClick = (row: RowItem) => alert("Row clicked: " + row.name);

export default {
  name: "DataTable",
  component: DataTable,
  props: [
    { name: "rows", value: rows, type: "json" },
    { name: "columns", value: columns, type: "json" },
    { name: "caption", value: caption, type: "text" },
    { name: "initialSort", value: initialSort, type: "json" },
    { name: "loading", value: loading, type: "bool" },
    { name: "onRowClick", value: onRowClick, type: "func" },
  ],
  stories: [],
};
