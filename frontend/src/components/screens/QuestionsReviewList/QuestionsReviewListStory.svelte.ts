import {
  CONSULTATION_ID,
  showNextFetchErrorMock,
  showNextFreeTextErrorMock,
  showNextMock,
  showNextNoMoreErrorMock,
} from "./mocks";
import QuestionsReviewList from "./QuestionsReviewList.svelte";
import { questionsData } from "./testData";

const consultationId = $state(CONSULTATION_ID);
const questions = $state(questionsData);

export default {
  name: "QuestionsReviewList",
  component: QuestionsReviewList,
  category: "Screens / Support",
  mocks: [showNextMock],
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
      mocks: [showNextFreeTextErrorMock],
    },
    {
      name: "Fetch Error",
      props: {
        consultationId,
        questions,
      },
      mocks: [showNextFetchErrorMock],
    },
    {
      name: "No More Responses Error",
      props: {
        consultationId,
        questions,
      },
      mocks: [showNextNoMoreErrorMock],
    },
  ],
};
