import { CONSULTATION_ID } from "./mocks";
import QuestionsReviewList from "./QuestionsReviewList.svelte";
import { questionsData } from "./testData";

const consultationId = $state(CONSULTATION_ID);
const questions = $state(questionsData);

export default {
  name: "QuestionsReviewList",
  component: QuestionsReviewList,
  category: "Screens / Support",
  mocks: [],
  props: [
    { name: "consultationId", value: consultationId, type: "text" },
    { name: "questions", value: questions, type: "json" },
  ],
  stories: [],
};
