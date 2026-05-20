import {
  getApiConsultationUrl,
  getApiQuestionsUrl,
} from "../../../global/routes";

export const CONSULTATION_ID = "test-consultation";

export const consultationMock = {
  url: getApiConsultationUrl(CONSULTATION_ID),
  body: {
    id: "5ae41198-94ed-4770-9914-264b54f62f5e",
    title: "Demo Consultation",
    code: "demo_consultation",
    stage: "finalising_themes",
    users: [
      {
        id: 15,
        email: "user@test.com",
        is_staff: true,
        created_at: "2025-12-01T12:02:53.268635Z",
      },
    ],
    created_at: "2025-11-03T13:51:12.067131Z",
  },
};

export const questionsMock = {
  url: getApiQuestionsUrl(CONSULTATION_ID),
  body: {
    count: 3,
    next: null,
    previous: null,
    results: [
      {
        id: "2d3bea3e-abd1-4231-80d9-41a974724731",
        number: 1,
        total_responses: 125,
        question_text:
          "What measures should we consider to better support and increase rural affordable housing?",
        has_free_text: true,
        has_multiple_choice: true,
        multiple_choice_answer: [
          {
            id: "2a210b53-0205-4249-a863-18c6636e0afb",
            text: "Support",
            response_count: 76,
          },
          {
            id: "74adb02d-1638-48f9-a512-b6a50d6be61a",
            text: "Oppose",
            response_count: 49,
          },
        ],
        proportion_of_audited_answers: 0.0,
        theme_status: "draft",
      },
      {
        id: "7b809f89-a7a0-4c31-b788-008eef73f396",
        number: 2,
        total_responses: 125,
        question_text:
          "Are there other ways in which we can ensure that development supports and does not compromise food production?",
        has_free_text: true,
        has_multiple_choice: false,
        multiple_choice_answer: [],
        proportion_of_audited_answers: 0.0,
        theme_status: "draft",
      },
      {
        id: "021b9599-35c3-42d5-afba-45aa691dfe53",
        number: 3,
        total_responses: 125,
        question_text:
          "What would be the most appropriate way to promote high percentage Social Rent/affordable housing developments?",
        has_free_text: true,
        has_multiple_choice: false,
        multiple_choice_answer: [],
        proportion_of_audited_answers: 0.0,
        theme_status: "draft",
      },
    ],
  },
};

export const questionsAllSignedOffMock = {
  url: getApiQuestionsUrl(CONSULTATION_ID),
  body: {
    ...questionsMock.body,
    results: questionsMock.body.results.map((item) => ({
      ...item,
      theme_status: "confirmed",
    })),
  },
};

export const consultationUpdateMock = {
  url: getApiConsultationUrl(CONSULTATION_ID),
  method: "PATCH",
};
