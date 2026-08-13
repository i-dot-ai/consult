import DemographicGroup from "./DemographicGroup.svelte";

const category = $state("Region");
const items = $state([
  { id: "1", name: "Region", value: "North", count: 30454 },
  { id: "2", name: "Region", value: "South", count: 30861 },
  { id: "3", name: "Region", value: "East", count: 30451 },
  { id: "4", name: "Region", value: "West", count: 30642 },
  { id: "5", name: "Region", value: "Central", count: 30454 },
]);
const countsLoading = $state(false);

export default {
  name: "DemographicGroup",
  component: DemographicGroup,
  category: "Dashboard",
  props: [
    { name: "category", value: category, type: "text" },
    { name: "items", value: items, type: "json" },
    { name: "countsLoading", value: countsLoading, type: "bool" },
  ],
  stories: [
    {
      name: "Default",
      props: { category: "Region", items, countsLoading: false },
    },
    {
      name: "Counts Loading",
      props: { category: "Region", items, countsLoading: true },
    },
  ],
};
