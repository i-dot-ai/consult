import Learnings from "./Learnings.svelte";
import { TEST_DATA } from "./testData";

const items = $state(TEST_DATA.items);
const id = $state();

export default {
  name: "Learnings",
  component: Learnings,
  category: "Data",
  props: [
    { name: "items", value: items, type: "json" },
    { name: "id", value: id, type: "text" },
  ],
  stories: [
    {
      name: "Empty",
      props: {
        items: [],
      },
    },
  ],
};
