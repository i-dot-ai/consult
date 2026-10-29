import {
  demographicAnswersQueryParts,
  demographicMergeQueryParts,
  questionsV2QueryParts,
  questionV2QueryParts,
} from "../../../global/queries/questions/parts";
import type {
  DemographicAnswer,
  QuestionV2,
} from "../../../global/queries/questions/types";

export const CONSULTATION_ID = "95ab7567-9381-48eb-8d20-ddeb43691b58";

export const QUESTIONS: QuestionV2[] = [
  {
    id: "q1-uuid",
    number: 1,
    text: "Do you agree with the proposed approach?",
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
    text: "Which region are you responding from?",
    type: "demographic",
    closed_question: null,
    short_name: "",
    dashboard_role: "filter",
    status: "configured",
    response_count: 6,
  },
  {
    id: "q3-uuid",
    number: 3,
    text: "Are you responding as an individual or an organisation?",
    type: "demographic",
    closed_question: null,
    short_name: "Respondent type",
    dashboard_role: "filter",
    status: "configured",
    response_count: 5,
  },
  {
    id: "q4-uuid",
    number: 4,
    text: "Please explain your answer.",
    type: "open",
    closed_question: "q1-uuid",
    short_name: "",
    dashboard_role: "filter",
    status: "configured",
    response_count: 380,
  },
  {
    id: "q7-uuid",
    number: 7,
    text: "Should penalties be linked to turnover?",
    type: "closed",
    closed_question: null,
    short_name: "",
    dashboard_role: "filter",
    status: "configured",
    response_count: 300,
  },
];

export const AGREEMENT_ANSWERS: DemographicAnswer[] = [
  { text: "Yes", count: 20, responses: ["y1", "y2"] },
  { text: "No", count: 10, responses: ["n1", "n2"] },
];

export const PENALTY_ANSWERS: DemographicAnswer[] = [
  { text: "Yes", count: 150, responses: ["p1", "p2"] },
  { text: "No", count: 90, responses: ["p3", "p4"] },
  { text: "Only for large companies", count: 40, responses: ["p5", "p6"] },
  { text: "Not sure", count: 20, responses: ["p7"] },
];

export const REGION_ANSWERS: DemographicAnswer[] = [
  { text: "England", count: 3, responses: ["e1", "e2", "e3"] },
  { text: "Scotland", count: 2, responses: ["s1", "s2"] },
  { text: "Wales", count: 1, responses: ["w1"] },
];

export const RESPONDENT_ANSWERS: DemographicAnswer[] = [
  { text: "Individual", count: 2, responses: ["i1", "i2"] },
  { text: "Organisation", count: 2, responses: ["o1", "o2"] },
  { text: "individual", count: 1, responses: ["i3"] },
];

export const MERGED_RESPONDENT_ANSWERS: DemographicAnswer[] = [
  { text: "Individual", count: 3, responses: ["i1", "i2", "i3"] },
  { text: "Organisation", count: 2, responses: ["o1", "o2"] },
];

export const SCALE_ANSWERS: DemographicAnswer[] = [
  { text: "Agree", count: 5, responses: ["a1", "a2", "a3", "a4", "a5"] },
  {
    text: "Neither agree nor disagree",
    count: 4,
    responses: ["n1", "n2", "n3", "n4"],
  },
  { text: "Strongly agree", count: 3, responses: ["sa1", "sa2", "sa3"] },
  { text: "Disagree", count: 2, responses: ["d1", "d2"] },
  { text: "Strongly disagree", count: 1, responses: ["sd1"] },
];

export const questionsMock = {
  url: questionsV2QueryParts.url(CONSULTATION_ID),
  body: QUESTIONS,
};

export const questionsErrorMock = {
  url: questionsV2QueryParts.url(CONSULTATION_ID),
  body: {},
  throws: new Error("Fetch failed"),
};

export const answersMock = (
  questionId: string,
  answers: DemographicAnswer[] | (() => DemographicAnswer[]),
) => ({
  url: demographicAnswersQueryParts.url(CONSULTATION_ID, questionId),
  body: answers,
});

export const answersErrorMock = (questionId: string) => ({
  url: demographicAnswersQueryParts.url(CONSULTATION_ID, questionId),
  status: 500,
  body: {},
});

export const mergeMock = (questionId: string) => ({
  url: demographicMergeQueryParts.url(CONSULTATION_ID, questionId),
  method: "POST",
  body: { new_value: "", responses: [] },
});

export const mergeErrorMock = (questionId: string) => ({
  ...mergeMock(questionId),
  status: 400,
  body: {
    responses: ["All responses must exist and belong to this question."],
  },
});

export const updateMock = (questionId: string) => ({
  url: questionV2QueryParts.url(CONSULTATION_ID, questionId),
  method: "PATCH",
  body: QUESTIONS.find((question) => question.id === questionId),
});
