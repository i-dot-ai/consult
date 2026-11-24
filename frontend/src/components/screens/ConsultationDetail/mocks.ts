export const CONSULTATION_ID = "test-consultation";

const DEMO_OPTIONS_URL = /\/api\/consultations\/.*\/demographic-options\//;
const QUESTIONS_URL = /\/api\/consultations\/.*\/questions\//;
const RESPONDENTS_URL = /\/api\/consultations\/.*\/respondents\//;

const QUESTIONS = [
  {
    id: "5e8176da-fdcd-4f55-ab7b-b2ca8a12a467",
    number: 1,
    total_response_count: 100,
    free_text_response_count: 80,
    multi_choice_response_count: 100,
    question_text:
      "Do you agree with the proposal to align the flavour categories of chocolate bars as outlined in the draft guidelines of the Chocolate Bar Regulation for the United Kingdom?",
    has_free_text: true,
    has_multiple_choice: true,
    multiple_choice_answer: [
      {
        text: "Yes",
        response_count: 99,
      },
      {
        text: "No answer",
        response_count: 17,
      },
      {
        text: "No",
        response_count: 18,
      },
      {
        text: "Don't know",
        response_count: 98,
      },
    ],
    proportion_of_audited_answers: 0.0,
    theme_status: "draft",
  },
  {
    id: "ef855675-af2b-4cfe-871d-ad108360e57a",
    number: 2,
    total_response_count: 100,
    free_text_response_count: 0,
    multi_choice_response_count: 100,
    question_text:
      "Do you agree with the proposal to align the flavour categories of chocolate bars as outlined in the draft guidelines of the Chocolate Bar Regulation for the United Kingdom?",
    has_free_text: false,
    has_multiple_choice: true,
    multiple_choice_answer: [
      {
        text: "No",
        response_count: 61,
      },
      {
        text: "Don't know",
        response_count: 58,
      },
      {
        text: "No answer",
        response_count: 64,
      },
      {
        text: "Yes",
        response_count: 58,
      },
    ],
    proportion_of_audited_answers: 0,
    theme_status: "draft",
  },
  {
    id: "92848794-2072-41c4-b3bf-78248a6995da",
    number: 3,
    total_response_count: 100,
    free_text_response_count: 0,
    multi_choice_response_count: 100,
    question_text:
      "Which of the following factors do you believe are important when considering the packaging of chocolate bars? Please select all that apply: a) Sustainability, b) Design, c) Cost-effectiveness, d) Durability, e) Brand recognition.",
    has_free_text: false,
    has_multiple_choice: true,
    multiple_choice_answer: [
      {
        text: "Design",
        response_count: 62,
      },
      {
        text: "Brand recognition",
        response_count: 56,
      },
      {
        text: "Cost-effectiveness",
        response_count: 63,
      },
      {
        text: "Durability",
        response_count: 66,
      },
      {
        text: "Sustainability",
        response_count: 63,
      },
    ],
    proportion_of_audited_answers: 0,
    theme_status: "draft",
  },
  {
    id: "b20f35ee-411b-4746-9029-1e9b02610dea",
    number: 4,
    total_response_count: 100,
    free_text_response_count: 100,
    multi_choice_response_count: 0,
    question_text:
      "What are your thoughts on how the current chocolate bar regulations could be improved to better address consumer needs and industry standards?",
    has_free_text: true,
    has_multiple_choice: false,
    multiple_choice_answer: [],
    proportion_of_audited_answers: 0.0,
    theme_status: "draft",
  },
];

export const demoOptionsMock = {
  url: DEMO_OPTIONS_URL,
  body: [],
};

export const defaultQuestionsMock = {
  url: QUESTIONS_URL,
  body: {
    count: 4,
    next: null,
    previous: null,
    results: QUESTIONS,
  },
};

export const emptyQuestionsMock = {
  url: QUESTIONS_URL,
  body: {
    count: 0,
    next: null,
    previous: null,
    results: [],
  },
};

export const longQuestionsMock = {
  url: QUESTIONS_URL,
  body: {
    count: 0,
    next: null,
    previous: null,
    results: Array(100)
      .fill(QUESTIONS.at(0))
      .map((item, index) => ({
        ...item,
        id: (index + 1).toString(),
        number: index + 1,
      })),
  },
};

const totalQuestionCount = QUESTIONS.reduce(
  (acc, curr) => acc + curr.total_response_count,
  0,
);
export const defaultRespondentsMock = {
  url: RESPONDENTS_URL,
  body: {
    count: totalQuestionCount,
    next: null,
    previous: null,
    // array of empty objects corresponding to total response count
    results: Array.from(Array(totalQuestionCount).keys()).map((_) => ({})),
  },
};

// --- V2 mocks -----------------------------------------------------------------

const V2_QUESTIONS_URL = /\/api\/v2\/consultations\/.*\/questions\//;
const V2_DEMO_OPTIONS_URL =
  /\/api\/v2\/consultations\/.*\/responses\/demographic-options\//;

const V2_QUESTIONS = QUESTIONS.map(
  ({
    question_text,
    has_free_text,
    has_multiple_choice: _has_multiple_choice,
    theme_status: _theme_status,
    ...rest
  }) => ({
    ...rest,
    text: question_text,
    // Hybrid originals stay open with their multi-choice answers attached
    type: has_free_text ? "open" : "closed",
    closed_question: null,
    short_name: "",
    dashboard_role: "filter",
    status: "configured",
    response_count: rest.free_text_response_count,
  }),
);

export const v2QuestionsMock = {
  url: V2_QUESTIONS_URL,
  body: V2_QUESTIONS,
};

export const v2DemoOptionsMock = {
  url: V2_DEMO_OPTIONS_URL,
  body: [
    { id: "demo-token-1", name: "Nation", value: "England", count: 40 },
    { id: "demo-token-2", name: "Nation", value: "Wales", count: 25 },
    { id: "demo-token-3", name: "Age", value: "18-35", count: 30 },
  ],
};
