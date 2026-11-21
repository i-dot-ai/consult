import { describe, expect, it } from "vitest";

import {
  getApiDemographicOptionsV2Url,
  getApiResponseFlagV2Url,
  getApiResponseMarkReadV2Url,
  getApiResponseThemesV2Url,
  getApiResponseV2Url,
  getApiResponsesMarkReadBulkV2Url,
  getApiResponsesV2Url,
  getApiQuestionResponsesV2Url,
} from "./routes";

describe("v2 response routes", () => {
  const consultationId = "consultation-id";
  const questionId = "question-id";
  const responseId = "response-id";

  it("builds the question-scoped responses url", () => {
    expect(getApiQuestionResponsesV2Url(consultationId, questionId)).toBe(
      "/api/v2/consultations/consultation-id/questions/question-id/responses/",
    );
  });

  it("builds the consultation-scoped responses urls", () => {
    expect(getApiResponsesV2Url(consultationId)).toBe(
      "/api/v2/consultations/consultation-id/responses/",
    );
    expect(getApiResponseV2Url(consultationId, responseId)).toBe(
      "/api/v2/consultations/consultation-id/responses/response-id/",
    );
  });

  it("builds the per-response action urls", () => {
    expect(getApiResponseFlagV2Url(consultationId, responseId)).toBe(
      "/api/v2/consultations/consultation-id/responses/response-id/toggle-flag/",
    );
    expect(getApiResponseMarkReadV2Url(consultationId, responseId)).toBe(
      "/api/v2/consultations/consultation-id/responses/response-id/mark-read/",
    );
    expect(getApiResponseThemesV2Url(consultationId, responseId)).toBe(
      "/api/v2/consultations/consultation-id/responses/response-id/themes/",
    );
    expect(getApiResponsesMarkReadBulkV2Url(consultationId)).toBe(
      "/api/v2/consultations/consultation-id/responses/mark-read-bulk/",
    );
  });

  it("builds the demographic options url", () => {
    expect(getApiDemographicOptionsV2Url(consultationId)).toBe(
      "/api/v2/consultations/consultation-id/responses/demographic-options/",
    );
  });
});
