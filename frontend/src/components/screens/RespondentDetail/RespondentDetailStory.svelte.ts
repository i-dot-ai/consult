import {
  CONSULTATION_ID,
  consultationQuestionsMock,
  QUESTION_ID,
  questionsMock,
  RESPONDENT_ID,
  respondentsMock,
  responsesMock,
  updateRespondentMock,
} from "./mocks";
import RespondentDetail from "./RespondentDetail.svelte";

const consultationId = $state(CONSULTATION_ID);
const questionId = $state(QUESTION_ID);
const respondentId = $state(RESPONDENT_ID);
const themefinderId = $state(1);

export default {
  name: "RespondentDetail",
  component: RespondentDetail,
  category: "Screens",
  mocks: [
    questionsMock,
    responsesMock,
    respondentsMock,
    consultationQuestionsMock,
    updateRespondentMock,
  ],
  props: [
    { name: "consultationId", value: consultationId, type: "text" },
    { name: "questionId", value: questionId, type: "text" },
    { name: "respondentId", value: respondentId, type: "text" },
    { name: "themefinderId", value: themefinderId, type: "number" },
  ],
  stories: [],
};
