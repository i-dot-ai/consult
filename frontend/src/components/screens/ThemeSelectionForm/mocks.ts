import { getApiQuestionResponse, getApiShowNextResponse } from "../../../global/routes";

export const CONSULTATION_ID = "test-consultation";
export const QUESTION_ID = "test-question";
export const RESPONSE_ID = "test-response";

export const showNextMock = {
  url: getApiShowNextResponse(CONSULTATION_ID, QUESTION_ID),
}
export const submitMock = {
  url: getApiQuestionResponse(CONSULTATION_ID, QUESTION_ID, RESPONSE_ID),
  method: "PATCH",
  body: ({ body }: { body: string }) => {
    alert(body);
  }
}