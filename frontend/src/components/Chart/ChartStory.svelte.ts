import ChartTest from "./ChartTest.svelte";

const data = $state([ 200, 400 ]);
const labels = $state([
    { count: 200, text: "first item" },
    { count: 400, text: "second item" },
]);
const legendId = $state("test-legend");
const interactive = $state(true);

const LONG_DATA = Array.from(Array(10).keys());
const LONG_LABELS = LONG_DATA.map((count) => ({ text: `Item ${count}`, count }));

export default {
  name: "Chart",
  component: ChartTest,
  props: [
    { name: "data", value: data, type: "json" },
    { name: "labels", value: labels, type: "json" },
    { name: "legendId", value: legendId, type: "text" },
    { name: "interactive", value: interactive, type: "bool" },
  ],
  stories: [
    {
      name: "Empty",
      props: {
        data: [],
        labels: [],
        legendId,
        interactive,
      },
    },
    {
      name: "Long",
      props: {
        data: LONG_DATA,
        labels: LONG_LABELS,
        legendId,
        interactive,
      },
    },
    {
      name: "Not Interactive",
      props: {
        data,
        labels,
        legendId,
        interactive: false,
      },
    },
  ],
};
