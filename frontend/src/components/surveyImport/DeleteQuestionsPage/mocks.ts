import { questions } from "../../../global/queries/questions";

export const CONSULTATION_ID = "95ab7567-9381-48eb-8d20-ddeb43691b58";

const QUESTIONS_URL = new RegExp(
  questions.list.url(CONSULTATION_ID).replace(CONSULTATION_ID, ".*"),
);

const QUESTION_1_ID = "q1-uuid";
const QUESTION_2_ID = "q2-uuid";
const QUESTION_3_ID = "q3-uuid";

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
];

export const questionsMock = {
  url: QUESTIONS_URL,
  body: { count: QUESTIONS.length, next: null, previous: null, results: QUESTIONS },
};

export const questionsErrorMock = {
  url: QUESTIONS_URL,
  body: {},
  throws: new Error("Fetch failed"),
};

export const deleteMock = (questionId: string) => ({
  url: new RegExp(`/api/consultations/.*/questions/${questionId}/`),
  method: "DELETE" as const,
  body: null,
  status: 204,
});
