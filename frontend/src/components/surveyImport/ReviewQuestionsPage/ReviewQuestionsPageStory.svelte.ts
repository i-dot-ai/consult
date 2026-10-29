import ReviewQuestionsPage from "./ReviewQuestionsPage.svelte";
import {
  CONSULTATION_ID,
  PROPOSED_PAIR,
  QUESTIONS,
  answersMock,
  questionsErrorMock,
  questionsMock,
  updateMock,
} from "./mocks";

const consultationId = $state(CONSULTATION_ID);
const updateMocks = QUESTIONS.map((question) => updateMock(question.id));
const answerMocks = QUESTIONS.map((question) =>
  answersMock(question.id, ["Yes", "No", "Not sure"]),
);

export default {
  name: "ReviewQuestionsPage",
  component: ReviewQuestionsPage,
  category: "Screens / Survey Import",
  mocks: [questionsMock, ...updateMocks, ...answerMocks],
  props: [{ name: "consultationId", value: consultationId, type: "text" }],
  stories: [
    {
      name: "Default",
      mocks: [questionsMock, ...updateMocks, ...answerMocks],
      props: { consultationId: CONSULTATION_ID },
    },
    {
      name: "Hybrid pair proposed",
      mocks: [
        { ...questionsMock, body: [PROPOSED_PAIR.closed, PROPOSED_PAIR.open] },
        ...updateMocks,
        ...answerMocks,
      ],
      props: { consultationId: CONSULTATION_ID },
    },
    {
      name: "Fetch Error",
      mocks: [questionsErrorMock],
      props: { consultationId: CONSULTATION_ID },
    },
  ],
};
