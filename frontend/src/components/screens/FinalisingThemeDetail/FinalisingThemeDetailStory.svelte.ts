import FinalisingThemeDetail from "./FinalisingThemeDetail.svelte";
import {
  candidateThemesGetMock,
  questionMock,
  candidateThemeSelectMock,
  selectedThemesGetMock,
  CONSULTATION_ID,
  QUESTION_ID,
  selectedThemesCreateMock,
  selectedThemesEditMock,
  selectedThemesDeleteMock,
  responsesGetMock,
} from "./mocks";

const consultationId = $state("test-consultation");
const questionId = $state("test-question");

export default {
  name: "FinalisingThemeDetail",
  component: FinalisingThemeDetail,
  category: "Screens",
  mocks: [
    questionMock,
    selectedThemesGetMock,
    candidateThemesGetMock,
    candidateThemeSelectMock,
    selectedThemesCreateMock,
    selectedThemesEditMock,
    selectedThemesDeleteMock,
    responsesGetMock,
  ],
  props: [
    { name: "consultationId", value: consultationId, type: "text" },
    { name: "questionId", value: questionId, type: "text" },
  ],
  stories: [
    {
      name: "Select Candidate Theme 5xx Error",
      mocks: [
        questionMock,
        selectedThemesGetMock,
        candidateThemesGetMock,
        {
          ...candidateThemeSelectMock,
          status: 500,
          callback: undefined,
        },
        selectedThemesCreateMock,
        selectedThemesEditMock,
        selectedThemesDeleteMock,
        responsesGetMock,
      ],
      props: { consultationId: CONSULTATION_ID, questionId: QUESTION_ID },
    },
    {
      name: "Select Candidate Theme Fetch Error",
      mocks: [
        questionMock,
        selectedThemesGetMock,
        candidateThemesGetMock,
        {
          ...candidateThemeSelectMock,
          throws: new Error("Fetch error"),
          callback: undefined,
        },
        selectedThemesCreateMock,
        selectedThemesEditMock,
        selectedThemesDeleteMock,
        responsesGetMock,
      ],
      props: { consultationId: CONSULTATION_ID, questionId: QUESTION_ID },
    },
    {
      name: "Edit Theme Conflict Version Error",
      mocks: [
        questionMock,
        selectedThemesGetMock,
        candidateThemesGetMock,
        candidateThemeSelectMock,
        selectedThemesCreateMock,
        {
          ...selectedThemesEditMock,
          status: 412,
          body: {
            last_modified_by: {
              email: "someotheruser@test.com",
            },
            latest_version: 5,
          },
        },
        selectedThemesDeleteMock,
        responsesGetMock,
      ],
      props: { consultationId: CONSULTATION_ID, questionId: QUESTION_ID },
    },
    {
      name: "Edit Theme Conflict 404 Error",
      mocks: [
        questionMock,
        selectedThemesGetMock,
        candidateThemesGetMock,
        candidateThemeSelectMock,
        selectedThemesCreateMock,
        {
          ...selectedThemesEditMock,
          status: 404,
          body: undefined,
        },
        selectedThemesDeleteMock,
        responsesGetMock,
      ],
      props: { consultationId: CONSULTATION_ID, questionId: QUESTION_ID },
    },
  ],
};
