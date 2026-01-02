import AnswersList from "./AnswersList.svelte";

const variant = $state("selected");
const title = $state("Test Title");
const answers = $state(["Answer 1", "Answer 2", "Answer 3"]);
const loading = $state(false);

export default {
  name: "AnswersList",
  component: AnswersList,
  category: "Theme Sign Off",
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
    {
      name: "loading",
      value: loading,
      type: "bool",
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
