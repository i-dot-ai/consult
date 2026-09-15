import DataTable from "./DataTable.svelte";
import { extraColumns, extraRows, TEST_DATA } from "./testData";

const rows = $state(TEST_DATA.rows);
const columns = $state(TEST_DATA.columns);
const caption = $state(TEST_DATA.caption);
const initialSort = $state(TEST_DATA.initialSort);
const loading = $state(TEST_DATA.loading);
const columnSelect = $state(TEST_DATA.columnSelect);
const searchable = $state(TEST_DATA.searchable);
const searchPlaceholder = $state(TEST_DATA.searchPlaceholder);
const sortable = $state(TEST_DATA.sortable);
const paginated = $state(TEST_DATA.paginated);
const pageSizes = $state(TEST_DATA.pageSizes);

export default {
  name: "DataTable",
  component: DataTable,
  props: [
    { name: "rows", value: rows, type: "json" },
    { name: "columns", value: columns, type: "json" },
    { name: "caption", value: caption, type: "text" },
    { name: "initialSort", value: initialSort, type: "json" },
    { name: "loading", value: loading, type: "bool" },
    { name: "onRowClick", value: TEST_DATA.onRowClick, type: "func" },
    { name: "columnSelect", value: columnSelect, type: "bool" },
    { name: "searchable", value: searchable, type: "bool" },
    { name: "sortable", value: sortable, type: "bool" },
    { name: "paginated", value: paginated, type: "bool" },
    { name: "pageSizes", value: pageSizes, type: "json" },
    { name: "searchPlaceholder", value: searchPlaceholder, type: "text" },
  ],
  stories: [
    {
      name: "Paginated",
      props: {
        ...TEST_DATA,
        pageSizes: [1, 3],
      },
    },
    {
      name: "Not Paginated",
      props: {
        ...TEST_DATA,
        paginated: false,
        pageSizes: [1],
      },
    },
    {
      name: "Loading",
      props: {
        ...TEST_DATA,
        loading: true,
      },
    },
    {
      name: "No Data",
      props: {
        ...TEST_DATA,
        rows: [],
        loading: false,
      },
    },
    {
      name: "More Columns",
      props: {
        ...TEST_DATA,
        columns: extraColumns,
        rows: extraRows,
      },
    },
    {
      name: "Not Sortable",
      props: {
        ...TEST_DATA,
        sortable: false,
      },
    },
  ],
};
