import Checklist from "./Checklist.svelte";
import { TEST_DATA } from "./testData";

const items = $state(TEST_DATA.items);
const title = $state(TEST_DATA.title);

const onChange = $state((id: string, checked: boolean) => {
  items.find((item) => item.id === id)!.checked = checked;
});

export default {
  name: "Checklist",
  component: Checklist,
  category: "data",
  props: [
    { name: "title", value: title, type: "text" },
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
