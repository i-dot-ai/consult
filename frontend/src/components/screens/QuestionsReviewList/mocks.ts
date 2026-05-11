import { getApiShowNextResponse } from "../../../global/routes";

export const CONSULTATION_ID = "test-consultation";

export const showNextMock = {
  regexp: "*host" + getApiShowNextResponse(":consultationId", ":questionId"),
  body: () => ({
    next_response: {
      consultation_id: CONSULTATION_ID,
      question_id: "test-question",
      id: "test-response",
    },
  })
}

export const showNextFreeTextErrorMock = {
  regexp: "*host" + getApiShowNextResponse(":consultationId", ":questionId"),
  body: () => ({
    has_free_text: false,
  })
}

export const showNextNoMoreErrorMock = {
  regexp: "*host" + getApiShowNextResponse(":consultationId", ":questionId"),
  body: () => ({
    has_free_text: true,
  })
}

export const showNextFetchErrorMock = {
  regexp: "*host" + getApiShowNextResponse(":consultationId", ":questionId"),
  throws: new Error("Fetch failed"),
}