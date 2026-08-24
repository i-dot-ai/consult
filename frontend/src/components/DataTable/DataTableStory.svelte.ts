import DataTable from "./DataTable.svelte";
import { CAPTION, COLUMNS, INITIAL_SORT, LOADING, onRowClick, ROWS } from "./testData";

const rows = $state(ROWS);
const columns = $state(COLUMNS);
const caption = $state(CAPTION);
const initialSort = $state(INITIAL_SORT);
const loading = $state(LOADING);

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
