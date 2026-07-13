import { columns } from "./columns";
import { DATA } from "./data";
import DataTable from "./DataTable.svelte";

export default {
  name: "DataTable",
  component: DataTable,
  category: "Example",
  props: [
    { name: "data", value: DATA, type: "json" },
    { name: "columns", value: columns, type: "json" },
  ],
  stories: [],
};
