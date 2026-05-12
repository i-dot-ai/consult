import {
  getApiGetSelectedThemesUrl,
  getApiQuestionUrl,
} from "../../../global/routes";

export const CONSULTATION_ID = "test-consultation";
export const QUESTION_ID = "test-question";

export const questionMock = {
  url: getApiQuestionUrl(CONSULTATION_ID, QUESTION_ID),
  body: {
    id: "5de28a81-0095-4863-b0a8-2234d88e483f",
    number: 4,
    total_responses: 100,
    question_text:
      "What are your thoughts on how the current chocolate bar regulations could be improved to better address consumer needs and industry standards?",
    has_free_text: true,
    has_multiple_choice: false,
    multiple_choice_answer: [],
    proportion_of_audited_answers: 0,
    theme_status: "confirmed",
  },
};

export const selectedThemesMock = {
  url: getApiGetSelectedThemesUrl(CONSULTATION_ID, QUESTION_ID),
  body: {
    count: 2,
    next: null,
    previous: null,
    results: [
      {
        id: "50a0aa3b-d3f3-4536-bc77-3dda65fa5743",
        name: "More innovative",
        description: "Innovative ideas to improve chocolate bar regulations.",
        version: 1,
        modified_at: "2026-01-29T14:23:17.097584Z",
        last_modified_by: null,
      },
      {
        id: "e5318f2f-49fa-4e2b-9c40-7110e0ce769e",
        name: "Innovative packaging",
        description: "Ideas for innovative packaging solutions.",
        version: 1,
        modified_at: "2026-01-29T14:23:17.099676Z",
        last_modified_by: null,
      },
    ],
  },
};

export const selectedThemeEmptyMock = {
  url: getApiGetSelectedThemesUrl(CONSULTATION_ID, QUESTION_ID),
  body: {
    count: 0,
    next: null,
    previous: null,
    results: [],
  },
};
