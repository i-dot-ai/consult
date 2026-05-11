import { CONSULTATION_ID, showNextFreeTextErrorMock, showNextMock } from "./mocks";
import QuestionsReviewList from "./QuestionsReviewList.svelte";
import { questionsData } from "./testData";

const consultationId = $state(CONSULTATION_ID);
const questions = $state(questionsData);

export default {
  name: "QuestionsReviewList",
  component: QuestionsReviewList,
  category: "Screens / Support",
  mocks: [
    showNextMock,
  ],
  props: [
    { name: "consultationId", value: consultationId, type: "text" },
    { name: "questions", value: questions, type: "json" },
  ],
  stories: [
    {
      name: "Free Text Error",
      props: {
        consultationId,
        questions,
      },
      mocks: [
        showNextFreeTextErrorMock,
      ]
    }
  ],
};
