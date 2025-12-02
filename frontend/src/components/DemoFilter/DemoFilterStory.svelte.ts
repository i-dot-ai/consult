import DemoFilter from "./DemoFilter.svelte";

const TEST_DATA = {
  category: "Country",
  demoOptions: { Country: ["England", "Scotland"] },
  demoData: { Country: { England: 10, Scotland: 20 } },
  totalCounts: { Country: 30 },
  skeleton: false,
};

const category = $state(TEST_DATA.category);
const demoOptions = $state(TEST_DATA.demoOptions);
const demoData = $state(TEST_DATA.demoData);
const totalCounts = $state(TEST_DATA.totalCounts);
const skeleton = $state(TEST_DATA.skeleton);

export default {
  name: "DemoFilter",
  component: DemoFilter,
  category: "Dashboard",
  props: [
    { name: "category", value: category, type: "text" },
    { name: "demoOptions", value: demoOptions, type: "json" },
    { name: "demoData", value: demoData, type: "json" },
    { name: "totalCounts", value: totalCounts, type: "json" },
    { name: "skeleton", value: skeleton, type: "bool" },
  ],
  stories: [
    {
      name: "Default",
      props: {
        ...TEST_DATA,
      },
    },
    {
      name: "Empty",
      props: {
        ...TEST_DATA,
        demoOptions: {},
        demoData: {},
        totalCounts: 0,
      },
    },
    {
      name: "Skeleton",
      props: {
        ...TEST_DATA,
        skeleton: true,
      },
    },
  ],
};
