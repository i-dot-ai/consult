import ResponsesList from "./ResponsesList.svelte";

const variant = $state("selected");
const title = $state("Test Title");
const responses = $state(["response 1", "response 2", "response 3"]);
const loading = $state(false);

export default {
  name: "ResponsesList",
  component: ResponsesList,
  category: "Finalising Themes",
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
      name: "No responses",
      props: {
        variant: "selected",
        responses: [],
        title: "No Responses Story",
      },
    },
  ],
};
