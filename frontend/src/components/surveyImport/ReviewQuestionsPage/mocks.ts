import {
  questionsV2QueryParts,
  questionV2QueryParts,
} from "../../../global/queries/questions/parts";
import type { QuestionV2 } from "../../../global/queries/questions/types";

export const CONSULTATION_ID = "95ab7567-9381-48eb-8d20-ddeb43691b58";

export const QUESTIONS: QuestionV2[] = [
  {
    id: "q1-uuid",
    number: 1,
    text: "Do you agree with the proposed zoning approach?",
    type: "closed",
    closed_question: null,
    short_name: "",
    dashboard_role: "filter",
    status: "configured",
    response_count: 412,
  },
  {
    id: "q2-uuid",
    number: 2,
    text: "Please explain your answer.",
    type: "open",
    closed_question: "q1-uuid",
    short_name: "",
    dashboard_role: "filter",
    status: "configured",
    response_count: 398,
  },
  {
    id: "q3-uuid",
    number: 3,
    text: "Which region are you responding from?",
    type: null,
    closed_question: null,
    short_name: "",
    dashboard_role: "filter",
    status: "draft",
    response_count: 412,
  },
  {
    id: "q4-uuid",
    number: 4,
    text: "What else should the framework cover?",
    type: "open",
    closed_question: null,
    short_name: "",
    dashboard_role: "filter",
    status: "configured",
    response_count: 380,
  },
  {
    id: "q5-uuid",
    number: 5,
    text: "Should penalties be linked to turnover?",
    type: "closed",
    closed_question: null,
    short_name: "",
    dashboard_role: "filter",
    status: "configured",
    response_count: 402,
  },
  {
    id: "q6-uuid",
    number: 6,
    text: "If not, please explain why",
    type: "open",
    closed_question: null,
    short_name: "",
    dashboard_role: "filter",
    status: "configured",
    response_count: 211,
  },
];

export const PROPOSED_PAIR = { closed: QUESTIONS[4], open: QUESTIONS[5] };

export const MANY_QUESTIONS: QuestionV2[] = Array.from(
  { length: 12 },
  (_, index) => ({
    id: `q${index + 1}-uuid`,
    number: index + 1,
    text: `Question ${index + 1}`,
    type: "open",
    closed_question: null,
    short_name: "",
    dashboard_role: "filter",
    status: "configured",
    response_count: 10,
  }),
);

export const questionsMock = {
  url: questionsV2QueryParts.url(CONSULTATION_ID),
  body: QUESTIONS,
};

export const questionsErrorMock = {
  url: questionsV2QueryParts.url(CONSULTATION_ID),
  body: {},
  throws: new Error("Fetch failed"),
};

export const answersMock = (questionId: string, answers: string[]) => ({
  url: new RegExp(
    `/api/consultations/[^/]+/questions/${questionId}/responses/`,
  ),
  body: {
    has_more_pages: false,
    next_cursor: null,
    total_count: answers.length,
    all_respondents: answers.map((text) => ({ free_text_answer_text: text })),
  },
});

export const updateMock = (
  questionId: string,
  body: Partial<QuestionV2> = {},
) => ({
  url: questionV2QueryParts.url(CONSULTATION_ID, questionId),
  method: "PATCH",
  body: {
    ...QUESTIONS.find((question) => question.id === questionId)!,
    ...body,
  },
});

export const updateErrorMock = (questionId: string) => ({
  ...updateMock(questionId),
  status: 400,
  body: { type: ['"hybrid" is not a valid choice.'] },
});
