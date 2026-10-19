import DeleteQuestionsPage from "./DeleteQuestionsPage.svelte";
import { CONSULTATION_ID, deleteMock, questionsErrorMock, questionsMock, QUESTIONS } from "./mocks";

const consultationId = $state(CONSULTATION_ID);

export default {
  name: "DeleteQuestionsPage",
  component: DeleteQuestionsPage,
  category: "Data",
  mocks: [questionsMock, deleteMock(QUESTIONS[0].id)],
  props: [{ name: "consultationId", value: consultationId, type: "text" }],
  stories: [
    {
      name: "Default",
      props: { consultationId: CONSULTATION_ID },
    },
    {
      name: "Fetch Error",
      mocks: [questionsErrorMock],
      props: { consultationId: CONSULTATION_ID },
    },
  ],
};
