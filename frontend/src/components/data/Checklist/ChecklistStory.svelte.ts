import Checklist from "./Checklist.svelte";
import { TEST_DATA } from "./testData";

const items = $state(TEST_DATA.items);

const onChange = $state((id: string, checked: boolean) => {
  items.find((item) => item.id === id)!.checked = checked;
});

export default {
  name: "Checklist",
  component: Checklist,
  category: "data",
  props: [
    { name: "items", value: items, type: "json" },
    { name: "onChange", value: onChange, type: "func" },
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
