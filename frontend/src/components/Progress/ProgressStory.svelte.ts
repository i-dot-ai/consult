import Progress from "./Progress.svelte";

export default {
  name: "Progress",
  component: Progress,
  props: [{ name: "value", value: 40, type: "number" }],
  stories: [
    {
      name: "Default",
      props: { value: 33 },
    },
    {
      name: "Full",
      props: { value: 100 },
    },
    {
      name: "Empty",
      props: { value: 0 },
    },
  ],
};
