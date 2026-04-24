import {
  CONSULTATION_ID,
  QUESTION_ID,
  questionMock,
  selectedThemeEmptyMock,
  selectedThemesMock,
} from "./mocks";
import ThemeSignOffDetailCompleted from "./ThemeSignOffDetailCompleted.svelte";

const consultationId = $state(CONSULTATION_ID);
const questionId = $state(QUESTION_ID);

export default {
  name: "ThemeSignOffDetailCompleted",
  component: ThemeSignOffDetailCompleted,
  category: "Screens",
  mocks: [questionMock, selectedThemesMock],
  props: [
    { name: "consultationId", value: consultationId, type: "text" },
    { name: "questionId", value: questionId, type: "text" },
  ],
  stories: [
    {
      name: "No Selected Themes",
      mocks: [questionMock, selectedThemeEmptyMock],
    },
    {
      name: "Selected Themes Fetch Error",
      mocks: [
        questionMock,
        { ...selectedThemesMock, throws: new Error("Fetch Error") },
      ],
    },
    {
      name: "Question Fetch Error",
      mocks: [
        { ...questionMock, throws: new Error("Fetch Error") },
        selectedThemesMock,
      ],
    },
    {
      name: "Selected Themes 5xx Error",
      mocks: [
        questionMock,
        { ...selectedThemesMock, status: 500, body: undefined },
      ],
    },
    {
      name: "Question 5xx Error",
      mocks: [
        { ...questionMock, status: 500, body: undefined },
        selectedThemesMock,
      ],
    },
    {
      name: "Selected Themes 4xx Error",
      mocks: [
        questionMock,
        { ...selectedThemesMock, status: 400, body: undefined },
      ],
    },
    {
      name: "Question 4xx Error",
      mocks: [
        { ...questionMock, status: 400, body: undefined },
        selectedThemesMock,
      ],
    },
  ],
};
