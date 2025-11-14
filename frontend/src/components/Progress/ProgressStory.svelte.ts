import Progress from "./Progress.svelte";

const value = $state(40);

export default {
  name: "Progress",
  component: Progress,
  props: [{ name: "value", value: value, type: "number" }],
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
