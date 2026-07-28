import ChartTest from "./ChartTest.svelte";
import { DATA, INTERACTIVE, LABELS, LEGEND_ID, LONG_DATA, LONG_LABELS } from "./testData";

const data = $state(DATA);
const labels = $state(LABELS);
const legendId = $state(LEGEND_ID);
const interactive = $state(INTERACTIVE);

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
