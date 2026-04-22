import ThemeSignOffDetail from "./ThemeSignOffDetail.svelte";
import { candidateThemesGetMock, questionMock, candidateThemeSelectMock, selectedThemesGetMock, CONSULTATION_ID, QUESTION_ID, selectedThemesCreateMock, selectedThemesEditMock } from "./mocks";

const consultationId = $state("test-consultation");
const questionId = $state("test-question");

export default {
  name: "ThemeSignOffDetail",
  component: ThemeSignOffDetail,
  category: "Screens",
  mocks: [
    questionMock,
    selectedThemesGetMock,
    candidateThemesGetMock,
    candidateThemeSelectMock,
    selectedThemesCreateMock,
    selectedThemesEditMock,
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
      ],
      props: { consultationId: CONSULTATION_ID, questionId: QUESTION_ID },
    },
  ],
};
