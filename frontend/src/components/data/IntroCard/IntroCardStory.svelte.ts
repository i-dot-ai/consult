import IntroCard from "./IntroCard.svelte";
import { TEST_DATA } from "./testData";

const icon = $state(TEST_DATA.icon);
const order = $state(TEST_DATA.order);
const title = $state(TEST_DATA.title);
const subtitle = $state(TEST_DATA.subtitle);

export default {
  name: "IntroCard",
  component: IntroCard,
  category: "Data",
  props: [
    { name: "Icon", value: icon },
    { name: "order", value: order, type: "number" },
    { name: "title", value: title, type: "text" },
    { name: "subtitle", value: subtitle, type: "text" },
  ],
  stories: [],
};
