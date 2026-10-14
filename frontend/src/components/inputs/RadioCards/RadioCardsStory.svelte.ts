import RadioCards from "./RadioCards.svelte";

const ITEMS = [
  { value: "qualtrics", text: "Qualtrics", hint: "Survey platform" },
  {
    value: "citizen-space",
    text: "Citizen Space",
    hint: "Consultation platform",
  },
];

const name = $state("tool");
const legend = $state("Which tool did you use?");
const hint = $state("Pick the one the responses were collected in.");
const items = $state(ITEMS);
const value = $state("qualtrics");

export default {
  name: "RadioCards",
  component: RadioCards,
  category: "Inputs",
  props: [
    { name: "name", value: name, type: "text" },
    { name: "legend", value: legend, type: "text" },
    { name: "hint", value: hint, type: "text" },
    { name: "items", value: items, type: "json" },
    { name: "value", value: value, type: "text" },
    { name: "onchange", value: () => {}, type: "func" },
  ],
  stories: [
    {
      name: "No Hints",
      props: {
        name: "tool",
        legend: "Which tool did you use?",
        items: ITEMS.map(({ value, text }) => ({ value, text })),
        value: "citizen-space",
        onchange: () => {},
      },
    },
  ],
};
