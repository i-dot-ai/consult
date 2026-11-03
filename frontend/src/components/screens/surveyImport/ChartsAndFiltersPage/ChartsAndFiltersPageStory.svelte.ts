import ChartsAndFiltersPage from "./ChartsAndFiltersPage.svelte";
import {
  AGREEMENT_ANSWERS,
  CONSULTATION_ID,
  PENALTY_ANSWERS,
  REGION_ANSWERS,
  RESPONDENT_ANSWERS,
  SCALE_ANSWERS,
  answersMock,
  mergeMock,
  questionsErrorMock,
  questionsMock,
} from "./mocks";

const consultationId = $state(CONSULTATION_ID);
const mergeMocks = [
  mergeMock("q1-uuid"),
  mergeMock("q2-uuid"),
  mergeMock("q3-uuid"),
  mergeMock("q7-uuid"),
];
const closedAnswerMocks = [
  answersMock("q1-uuid", AGREEMENT_ANSWERS),
  answersMock("q7-uuid", PENALTY_ANSWERS),
];

export default {
  name: "ChartsAndFiltersPage",
  component: ChartsAndFiltersPage,
  category: "Screens / Survey Import",
  mocks: [
    questionsMock,
    answersMock("q2-uuid", REGION_ANSWERS),
    answersMock("q3-uuid", RESPONDENT_ANSWERS),
    ...closedAnswerMocks,
    ...mergeMocks,
  ],
  props: [{ name: "consultationId", value: consultationId, type: "text" }],
  stories: [
    {
      name: "Default",
      mocks: [
        questionsMock,
        answersMock("q2-uuid", REGION_ANSWERS),
        answersMock("q3-uuid", RESPONDENT_ANSWERS),
        ...closedAnswerMocks,
        ...mergeMocks,
      ],
      props: { consultationId: CONSULTATION_ID },
    },
    {
      name: "Scale answers",
      mocks: [
        questionsMock,
        answersMock("q2-uuid", SCALE_ANSWERS),
        answersMock("q3-uuid", RESPONDENT_ANSWERS),
        ...closedAnswerMocks,
        ...mergeMocks,
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
