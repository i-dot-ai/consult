import DataTable from "./DataTable.svelte";
import { extraColumns, extraRows, TEST_DATA } from "./testData";

const rows = $state(TEST_DATA.rows);
const columns = $state(TEST_DATA.columns);
const caption = $state(TEST_DATA.caption);
const initialSort = $state(TEST_DATA.initialSort);
const loading = $state(TEST_DATA.loading);

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
  ],
};
