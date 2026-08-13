import IntroCard from "./IntroCard.svelte";
import { TEST_DATA } from "./testData";

const Icon = $state(TEST_DATA.Icon);
const steps = $state(TEST_DATA.steps);
const title = $state(TEST_DATA.title);
const subtitle = $state(TEST_DATA.subtitle);
const isActive = $state(TEST_DATA.isActive);
const showArrow = $state(TEST_DATA.showArrow);

export default {
  name: "IntroCard",
  component: IntroCard,
  category: "Data",
  props: [
    { name: "Icon", value: Icon },
    { name: "steps", value: steps, type: "json" },
    { name: "title", value: title, type: "text" },
    { name: "subtitle", value: subtitle, type: "text" },
    { name: "isActive", value: isActive, type: "bool" },
    { name: "showArrow", value: showArrow, type: "bool" },
  ],
  stories: [
    { name: "inactive", props: { ...TEST_DATA, isActive: false } },
    { name: "no arrow", props: { ...TEST_DATA, showArrow: false } },
    {
      name: "inactive no arrow",
      props: { ...TEST_DATA, isActive: false, showArrow: false },
    },
  ],
};
