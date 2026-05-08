import { CONSULTATION_ID, QUESTION_ID, RESPONSE_ID } from "./mocks";
import { allThemes, selectedThemes } from "./testData";
import ThemeSelectionForm from "./ThemeSelectionForm.svelte";

const consultationId = $state(CONSULTATION_ID);
const questionId = $state(QUESTION_ID);
const responseId = $state(RESPONSE_ID);


export default {
  name: "ThemeSelectionForm",
  component: ThemeSelectionForm,
  category: "Screens / Support",
  mocks: [],
  props: [
    { name: "consultationId", value: consultationId, type: "text" },
    { name: "questionId", value: questionId, type: "text" },
    { name: "responseId", value: responseId, type: "text" },
    { name: "allThemes", value: allThemes, type: "json" },
    { name: "selectedThemes", value: selectedThemes, type: "json" },
  ],
  stories: [],
};
