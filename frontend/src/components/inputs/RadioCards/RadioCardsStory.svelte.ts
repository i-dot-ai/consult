import RadioCards from "./RadioCards.svelte";

const ITEMS = [
  { value: "email", text: "Email", hint: "Replies go to your inbox" },
  { value: "phone", text: "Phone", hint: "We call you back" },
];

const name = $state("contact");
const legend = $state("How should we contact you?");
const hint = $state("Pick the one you check most often.");
const items = $state(ITEMS);
const value = $state("email");

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
        name: "contact",
        legend: "How should we contact you?",
        items: ITEMS.map(({ value, text }) => ({ value, text })),
        value: "phone",
        onchange: () => {},
      },
    },
  ],
};
