import RepresentativeResponses from "./RepresentativeResponses.svelte";

const consultationId = $state("consultation-id");
const questionId = $state("question-id");
const themeName = $state("Test Theme");
const themeDescription = $state("Test theme description");
const themeId = $state("theme-id");
const variant = $state("selected");

export default {
  name: "RepresentativeResponses",
  component: RepresentativeResponses,
  category: "Theme Sign Off",
  props: [
    {
      name: "consultationId",
      value: consultationId,
      type: "string",
    },
    {
      name: "questionId",
      value: questionId,
      type: "string",
    },
    {
      name: "themeName",
      value: themeName,
      type: "string",
    },
    {
      name: "themeDescription",
      value: themeDescription,
      type: "string",
    },
    {
      name: "themeId",
      value: themeId,
      type: "string",
    },
    {
      name: "variant",
      value: variant,
      type: "select",
      options: [
        { value: "selected", label: "Selected" },
        { value: "candidate", label: "Candidate" },
      ],
    },
  ],
  stories: [],
};
