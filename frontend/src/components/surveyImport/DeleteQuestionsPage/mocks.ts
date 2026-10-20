export const CONSULTATION_ID = "95ab7567-9381-48eb-8d20-ddeb43691b58";

const QUESTIONS_URL = /\/api\/consultations\/[^/]+\/questions\/([\?]|$)/; // eslint-disable-line no-useless-escape

const QUESTION_1_ID = "q1-uuid";
const QUESTION_2_ID = "q2-uuid";
const QUESTION_3_ID = "q3-uuid";
export const FREE_TEXT_QUESTION_ID = "q4-uuid";

export const QUESTIONS = [
  {
    id: QUESTION_1_ID,
    number: 1,
    question_text: "Response ID",
    total_response_count: 412,
    free_text_response_count: 0,
    multi_choice_response_count: 412,
    has_free_text: false,
    has_multiple_choice: true,
    multiple_choice_answer: [
      { id: "a1", text: "R_1Fz8kQp2LmXa9Tb", response_count: 1 },
      { id: "a2", text: "R_3kD9xQwN7vYpE2c", response_count: 1 },
      { id: "a3", text: "R_2aB7cD4eF6gH8iJ", response_count: 1 },
    ],
    proportion_of_audited_answers: 0,
    theme_status: "pending",
  },
  {
    id: QUESTION_2_ID,
    number: 2,
    question_text: "Start date",
    total_response_count: 412,
    free_text_response_count: 0,
    multi_choice_response_count: 412,
    has_free_text: false,
    has_multiple_choice: true,
    multiple_choice_answer: [
      { id: "b1", text: "01/01/2024", response_count: 100 },
    ],
    proportion_of_audited_answers: 0,
    theme_status: "pending",
  },
  {
    id: QUESTION_3_ID,
    number: 3,
    question_text: "What is your respondent type?",
    total_response_count: 387,
    free_text_response_count: 0,
    multi_choice_response_count: 387,
    has_free_text: false,
    has_multiple_choice: true,
    multiple_choice_answer: [
      { id: "c1", text: "Individual", response_count: 200 },
      { id: "c2", text: "Organisation", response_count: 187 },
    ],
    proportion_of_audited_answers: 0,
    theme_status: "pending",
  },
  {
    id: FREE_TEXT_QUESTION_ID,
    number: 4,
    question_text: "What factors should be considered?",
    total_response_count: 150,
    free_text_response_count: 150,
    multi_choice_response_count: 0,
    has_free_text: true,
    has_multiple_choice: false,
    multiple_choice_answer: [],
    proportion_of_audited_answers: 0,
    theme_status: "pending",
  },
];

export const questionsMock = {
  url: QUESTIONS_URL,
  body: {
    count: QUESTIONS.length,
    next: null,
    previous: null,
    results: QUESTIONS,
  },
};

export const questionsErrorMock = {
  url: QUESTIONS_URL,
  body: {},
  throws: new Error("Fetch failed"),
};

export const freeTextResponsesMock = {
  url: /\/questions\/q4-uuid\/responses\//,
  body: {
    count: 150,
    next: null,
    previous: null,
    results: [
      { free_text_answer_text: "Consider the environmental impact." },
      { free_text_answer_text: "Focus on economic feasibility." },
      { free_text_answer_text: "Ensure public consultation is thorough." },
    ],
  },
};

export const deleteMock = (questionId: string) => ({
  url: new RegExp(`/api/consultations/.*/questions/${questionId}/`),
  method: "DELETE" as const,
  body: null,
  status: 204,
});
