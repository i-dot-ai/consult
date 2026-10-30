import {
  getApiQuestionDemographicsMergeV2Url,
  getApiQuestionDemographicsV2Url,
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

export const demographicAnswersQueryParts = {
  url: (consultationId: string, questionId: string) =>
    getApiQuestionDemographicsV2Url(consultationId, questionId),
};

export const demographicMergeQueryParts = {
  url: (consultationId: string, questionId: string) =>
    getApiQuestionDemographicsMergeV2Url(consultationId, questionId),
};
