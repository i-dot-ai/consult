import {
  responsesEditMock,
  responsesUpdateMock,
  CONSULTATION_ID,
  consultationMock,
  demoMock,
  flagMock,
  QUESTION_ID,
  questionMock,
  themesMock,
  responsesMock,
} from "./mocks";
import QuestionDetail from "./QuestionDetail.svelte";

const consultationId = $state(CONSULTATION_ID);
const questionId = $state(QUESTION_ID);

export default {
  name: "QuestionDetail",
  component: QuestionDetail,
  category: "Screens",
  mocks: [
    consultationMock,
    questionMock,
    themesMock,
    flagMock,
    responsesMock,
    demoMock,
    responsesUpdateMock,
    responsesEditMock,
  ],
  props: [
    { name: "consultationId", value: consultationId, type: "text" },
    { name: "questionId", value: questionId, type: "text" },
  ],
  stories: [],
};
