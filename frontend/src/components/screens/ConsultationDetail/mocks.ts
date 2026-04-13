const DEMO_OPTIONS_URL = /\/api\/consultations\/.*\/demographic-options\//;
const QUESTIONS_URL = /\/api\/consultations\/.*\/questions\//;

const QUESTIONS = [
  {
    id: "5e8176da-fdcd-4f55-ab7b-b2ca8a12a467",
    number: 1,
    total_responses: 100,
    question_text:
      "Do you agree with the proposal to align the flavour categories of chocolate bars as outlined in the draft guidelines of the Chocolate Bar Regulation for the United Kingdom?",
    has_free_text: true,
    has_multiple_choice: true,
    multiple_choice_answer: [
      {
        id: "c0dd6e81-9503-4156-bf9e-548efd975cf8",
        text: "Yes",
        response_count: 99,
      },
      {
        id: "171f1142-d62f-4f70-aeb0-1fe738ad4789",
        text: "No answer",
        response_count: 17,
      },
      {
        id: "7448a8bd-fb8a-464f-a07b-7250299daa26",
        text: "No",
        response_count: 18,
      },
      {
        id: "7adf9e67-86ee-4848-8c1b-8a668c0f6c3c",
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
    total_responses: 100,
    question_text:
      "Do you agree with the proposal to align the flavour categories of chocolate bars as outlined in the draft guidelines of the Chocolate Bar Regulation for the United Kingdom?",
    has_free_text: false,
    has_multiple_choice: true,
    multiple_choice_answer: [
      {
        id: "faa06d2c-356d-46bf-84a3-3a3f8d55f0e8",
        text: "No",
        response_count: 61,
      },
      {
        id: "c40a3342-c98b-4ebf-b753-a7278de28829",
        text: "Don't know",
        response_count: 58,
      },
      {
        id: "5b74f470-4b8f-4f05-8458-3c182b17e49d",
        text: "No answer",
        response_count: 64,
      },
      {
        id: "5c78ec82-20c8-44c2-8a8a-2207a9c34a81",
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
    total_responses: 100,
    question_text:
      "Which of the following factors do you believe are important when considering the packaging of chocolate bars? Please select all that apply: a) Sustainability, b) Design, c) Cost-effectiveness, d) Durability, e) Brand recognition.",
    has_free_text: false,
    has_multiple_choice: true,
    multiple_choice_answer: [
      {
        id: "28a76cea-e243-4cdc-9ebc-2f7847b7891d",
        text: "Design",
        response_count: 62,
      },
      {
        id: "2834a9e7-d57e-4d6b-b324-18b2ee0ed7d5",
        text: "Brand recognition",
        response_count: 56,
      },
      {
        id: "d8290922-fa60-4e75-8184-21b643489e05",
        text: "Cost-effectiveness",
        response_count: 63,
      },
      {
        id: "c72c2e69-94da-466c-8589-81fb0c9d8e18",
        text: "Durability",
        response_count: 66,
      },
      {
        id: "8eb356c1-d936-4fab-bd36-e94db28c9f8a",
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
    total_responses: 100,
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
  response: () => [],
};

export const defaultQuestionsMock = {
  url: QUESTIONS_URL,
  response: () => ({
    count: 4,
    next: null,
    previous: null,
    results: QUESTIONS,
  }),
};

export const emptyQuestionsMock = {
  url: QUESTIONS_URL,
  response: {
    count: 0,
    next: null,
    previous: null,
    results: [],
  },
};

export const longQuestionsMock = {
  url: QUESTIONS_URL,
  response: {
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
