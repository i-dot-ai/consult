import {
  getApiShowNextResponse,
  getApiShowNextResponseV2Url,
} from "../../../global/routes";

export const CONSULTATION_ID = "test-consultation";

export const showNextMock = {
  regexp: "*host" + getApiShowNextResponse(":consultationId", ":questionId"),
  body: () => ({
    next_response: {
      consultation_id: CONSULTATION_ID,
      question_id: "test-question",
      id: "test-response",
    },
  }),
};

export const showNextFreeTextErrorMock = {
  regexp: "*host" + getApiShowNextResponse(":consultationId", ":questionId"),
  body: () => ({
    has_free_text: false,
  }),
};

export const showNextNoMoreErrorMock = {
  regexp: "*host" + getApiShowNextResponse(":consultationId", ":questionId"),
  body: () => ({
    has_free_text: true,
  }),
};

export const showNextFetchErrorMock = {
  regexp: "*host" + getApiShowNextResponse(":consultationId", ":questionId"),
  throws: new Error("Fetch failed"),
};

// --- V2 mocks -----------------------------------------------------------------

export const v2ClosedQuestion = {
  id: "9c1cd5db-e7e3-4470-a38b-4ff7dbd4cf64",
  number: 1,
  text: "Closed question",
  type: "closed",
  closed_question: null,
  short_name: "",
  dashboard_role: "filter",
  status: "configured",
  total_response_count: 0,
  free_text_response_count: 0,
  multi_choice_response_count: 0,
  multiple_choice_answer: [],
  proportion_of_audited_answers: 0,
};

export const showNextV2Mock = {
  regexp:
    "*host" + getApiShowNextResponseV2Url(":consultationId", ":questionId"),
  body: () => ({
    next_response: {
      consultation_id: CONSULTATION_ID,
      question_id: "test-question",
      id: "test-response",
    },
    type: "open",
    message: "Next response found.",
  }),
};

export const showNextV2FreeTextErrorMock = {
  regexp:
    "*host" + getApiShowNextResponseV2Url(":consultationId", ":questionId"),
  body: () => ({
    next_response: null,
    type: "closed",
    message: "This question does not have free text responses.",
  }),
};
