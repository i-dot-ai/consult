import {
  getApiQuestionsV2Url,
  getApiQuestionV2Url,
  Suffixes,
} from "../../routes";

export const questionsV2QueryParts = {
  key: (consultationId: string) => [Suffixes.Questions, "v2", consultationId],
  url: (consultationId: string) => getApiQuestionsV2Url(consultationId),
};

export const questionV2QueryParts = {
  url: (consultationId: string, questionId: string) =>
    getApiQuestionV2Url(consultationId, questionId),
};
