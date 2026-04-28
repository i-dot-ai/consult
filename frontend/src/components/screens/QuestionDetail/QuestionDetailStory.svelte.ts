import { answersMock, answerUpdateMock, CONSULTATION_ID, consultationMock, demoMock, QUESTION_ID, questionMock, themesMock } from "./mocks";
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
    answersMock,
    demoMock,
    answerUpdateMock,
  ],
  props: [
    { name: "consultationId", value: consultationId, type: "text" },
    { name: "questionId", value: questionId, type: "text" },
  ],
  stories: [],
};
