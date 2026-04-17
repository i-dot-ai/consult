import {
  getApiConsultationUrl,
  getApiQuestionsUrl,
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
        email: "email@example.com",
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
        total_responses: 100,
        question_text:
          "Do you agree with the proposal to align the flavour categories of chocolate bars as outlined in the draft guidelines of the Chocolate Bar Regulation for the United Kingdom?",
        has_free_text: true,
        has_multiple_choice: true,
        multiple_choice_answer: [
          {
            id: "28a0de43-cc2b-4a63-acd5-1bab418c494d",
            text: "No",
            response_count: 50,
          },
          {
            id: "7e79bb14-aed0-43c1-b0ba-c6c22820dc62",
            text: "Don't know",
            response_count: 99,
          },
          {
            id: "a2ad2b8f-c197-4d6d-9a51-5a89bca5f678",
            text: "Yes",
            response_count: 51,
          },
          {
            id: "94eec8bf-bb65-4099-ac0f-2a2b9b2eaed4",
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
        total_responses: 100,
        question_text:
          "Do you agree with the proposal to align the flavour categories of chocolate bars as outlined in the draft guidelines of the Chocolate Bar Regulation for the United Kingdom?",
        has_free_text: false,
        has_multiple_choice: true,
        multiple_choice_answer: [
          {
            id: "007f237a-c413-4c81-ab56-4036c23ae96e",
            text: "Don't know",
            response_count: 61,
          },
          {
            id: "e8327c24-b459-4e6d-ae05-c30cb30cf356",
            text: "Yes",
            response_count: 64,
          },
          {
            id: "bb0ede2f-23ea-4171-b903-cd9440b7d0ec",
            text: "No answer",
            response_count: 61,
          },
          {
            id: "762acea8-eac1-4924-8bfe-eb63be3de9c1",
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
        total_responses: 100,
        question_text:
          "Which of the following factors do you believe are important when considering the packaging of chocolate bars? Please select all that apply: a) Sustainability, b) Design, c) Cost-effectiveness, d) Durability, e) Brand recognition.",
        has_free_text: false,
        has_multiple_choice: true,
        multiple_choice_answer: [
          {
            id: "7d231203-1e53-4fe2-b198-4bcccffb1c10",
            text: "Cost-effectiveness",
            response_count: 56,
          },
          {
            id: "eb65ae06-f13a-4142-984b-6abfa042c841",
            text: "Sustainability",
            response_count: 64,
          },
          {
            id: "5841a773-372e-43bc-b91f-61a21ff7f87f",
            text: "Durability",
            response_count: 75,
          },
          {
            id: "d460a9e1-8dd6-4c8a-b1fd-1e4fbead9c1d",
            text: "Design",
            response_count: 60,
          },
          {
            id: "a4c2e7b3-004c-47e0-a71f-f9967996ac85",
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
        total_responses: 100,
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
