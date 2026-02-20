import Checklist from "./Checklist.svelte";
import { TEST_DATA } from "./testData";

const items = $state(TEST_DATA.items);

export default {
  name: "Checklist",
  component: Checklist,
  category: "data",
  props: [{ name: "items", value: items, type: "json" }],
  stories: [
    {
      name: "Empty",
      props: {
        items: [],
      },
    },
  ],
};
