import AnswersList from "./AnswersList.svelte";

let variant = $state("selected");
let title = $state("Test Title");
let answers = $state([
  "Answer 1",
  "Answer 2",
  "Answer 3",
]);

export default {
  name: "AnswersList",
  component: AnswersList,
  category: "Theme Signoff",
  props: [
    {
      name: "variant",
      value: variant,
      type: "select",
      options: [
        { value: "selected", label: "Selected" },
        { value: "generated", label: "Generated" },
      ],
    },
    {
      name: "title",
      value: title,
      type: "text",
    },
    {
      name: "answers",
      value: answers,
      type: "json",
    },
  ],
  stories: [
    {
      name: "No Answers",
      props: {
        variant: "selected",
        answers: [],
        title: "No Answers Story",
      },
    },
  ],
};
