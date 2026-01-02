import Progress from "./Progress.svelte";

export default {
  name: "Progress",
  component: Progress,
  props: [
    { name: "value", value: 40, type: "number" },
    {
      name: "thickness",
      value: 40,
      type: "select",
      options: [
        { value: 1, label: "1" },
        { value: 1.5, label: "1.5" },
        { value: 2, label: "2" },
      ]
    },
    { name: "transitionDelay", value: 0, type: "number" },
    { name: "transitionDuration", value: 300, type: "number" },
  ],
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
