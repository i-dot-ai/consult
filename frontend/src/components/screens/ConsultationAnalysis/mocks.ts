import {
  getApiConsultationUrl,
  getApiConsultationV2Url,
  getApiDemographicOptionsV2Url,
  getApiQuestionsUrl,
  getApiQuestionsV2Url,
} from "../../../global/routes";

export const CONSULTATION_ID = "test-consultation";
export const consultationMock = {
  url: getApiConsultationUrl(CONSULTATION_ID),
  body: {
    id: "95ab7567-9381-48eb-8d20-ddeb43691b58",
    title: "Dummy Consultation at Analysis Stage",
    code: "",
    stage: "analysis",
    users: [
      {
        id: 1,
        email: "admin@example.com",
        is_staff: true,
        created_at: "2026-01-29T14:15:50.850685Z",
      },
    ],
    created_at: "2026-01-29T14:23:14.719743Z",
  },
};

export const questionsMock = {
  url: getApiQuestionsUrl(CONSULTATION_ID),
  body: {
    count: 4,
    next: null,
    previous: null,
    results: [
      {
        id: "42d9ae23-caf6-494a-b3bd-1586c16feff1",
        number: 1,
        total_response_count: 100,
        free_text_response_count: 100,
        multi_choice_response_count: 0,
        question_text:
          "Do you agree with the proposal to align the flavour categories of chocolate bars as outlined in the draft guidelines of the Chocolate Bar Regulation for the United Kingdom?",
        has_free_text: true,
        has_multiple_choice: true,
        multiple_choice_answer: [
          {
            text: "No",
            response_count: 50,
          },
          {
            text: "Don't know",
            response_count: 99,
          },
          {
            text: "Yes",
            response_count: 51,
          },
          {
            text: "No answer",
            response_count: 50,
          },
        ],
        proportion_of_audited_answers: 0.0,
        theme_status: "confirmed",
      },
      {
        id: "e30009f9-21e2-4f08-b42b-86da2c556b4a",
        number: 2,
        total_response_count: 100,
        free_text_response_count: 100,
        multi_choice_response_count: 0,
        question_text:
          "Do you agree with the proposal to align the flavour categories of chocolate bars as outlined in the draft guidelines of the Chocolate Bar Regulation for the United Kingdom?",
        has_free_text: false,
        has_multiple_choice: true,
        multiple_choice_answer: [
          {
            text: "Don't know",
            response_count: 61,
          },
          {
            text: "Yes",
            response_count: 64,
          },
          {
            text: "No answer",
            response_count: 61,
          },
          {
            text: "No",
            response_count: 72,
          },
        ],
        proportion_of_audited_answers: 0,
        theme_status: "confirmed",
      },
      {
        id: "a97566ad-3b04-44ff-a195-875a44f0940b",
        number: 3,
        total_response_count: 100,
        free_text_response_count: 100,
        multi_choice_response_count: 0,
        question_text:
          "Which of the following factors do you believe are important when considering the packaging of chocolate bars? Please select all that apply: a) Sustainability, b) Design, c) Cost-effectiveness, d) Durability, e) Brand recognition.",
        has_free_text: false,
        has_multiple_choice: true,
        multiple_choice_answer: [
          {
            text: "Cost-effectiveness",
            response_count: 56,
          },
          {
            text: "Sustainability",
            response_count: 64,
          },
          {
            text: "Durability",
            response_count: 75,
          },
          {
            text: "Design",
            response_count: 60,
          },
          {
            text: "Brand recognition",
            response_count: 68,
          },
        ],
        proportion_of_audited_answers: 0,
        theme_status: "confirmed",
      },
      {
        id: "5de28a81-0095-4863-b0a8-2234d88e483f",
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
        theme_status: "confirmed",
      },
    ],
  },
};

export const demoOptionsMock = {
  url: `/api/consultations/${CONSULTATION_ID}/demographic-options/`,
  body: [],
};

// --- V2 mocks -----------------------------------------------------------------

export const consultationV2Mock = {
  url: getApiConsultationV2Url(CONSULTATION_ID),
  body: { ...consultationMock.body },
};

export const v2QuestionsMock = {
  url: getApiQuestionsV2Url(CONSULTATION_ID),
  body: questionsMock.body.results.map(
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
      status: "confirmed",
      response_count: rest.free_text_response_count,
    }),
  ),
};

export const v2DemoOptionsMock = {
  url: getApiDemographicOptionsV2Url(CONSULTATION_ID),
  body: [
    { id: "demo-token-1", name: "Nation", value: "England", count: 40 },
    { id: "demo-token-2", name: "Nation", value: "Wales", count: 25 },
  ],
};
