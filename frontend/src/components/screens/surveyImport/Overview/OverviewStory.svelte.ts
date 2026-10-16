import Overview from "./Overview.svelte";

const consultationId = $state("test-consultation");

export default {
  name: "Overview",
  component: Overview,
  category: "Screens / Survey Import",
  mocks: [],
  props: [{ name: "consultationId", value: consultationId, type: "text" }],
  stories: [],
};
