import RepresentativeResponses from "./RepresentativeResponses.svelte";

const variant = $state("selected");
const title = $state("Test Title");
const responses = $state(["Answer 1", "Answer 2", "Answer 3"]);
const loading = $state(false);

export default {
  name: "RepresentativeResponses",
  component: RepresentativeResponses,
  category: "Theme Sign Off",
  props: [
    {
      name: "variant",
      value: variant,
      type: "select",
      options: [
        { value: "selected", label: "Selected" },
        { value: "candidate", label: "Candidate" },
      ],
    },
    {
      name: "title",
      value: title,
      type: "text",
    },
    {
      name: "responses",
      value: responses,
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
        responses: [],
        title: "No Answers Story",
      },
    },
  ],
};
