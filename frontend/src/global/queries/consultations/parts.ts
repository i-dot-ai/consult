import {
  getApiConsultationDeepValidationUrl,
  getApiConsultationsRootUrl,
  getApiConsultationUploadUrl,
  getApiConsultationUrl,
  getApiConsultationV2Url,
  Routes,
  Suffixes,
} from "../../routes";

export const consultationsQueryParts = {
  key: () => [Suffixes.Consultations],
  url: () => `${Routes.ApiConsultations}?scope=assigned`,
};

export const consultationsV2QueryParts = {
  key: () => [Suffixes.Consultations, "v2"],
  url: () => getApiConsultationsRootUrl(),
};

export const consultationQueryParts = {
  key: (consultationId: string) => [Suffixes.Consultations, consultationId],
  url: (consultationId: string) => getApiConsultationUrl(consultationId),
};

export const consultationV2QueryParts = {
  key: (consultationId: string) => [
    Suffixes.Consultations,
    "v2",
    consultationId,
  ],
  url: (consultationId: string) => getApiConsultationV2Url(consultationId),
};

export const consultationV2DeepValidationQueryParts = {
  key: (consultationId: string) => [Suffixes.Consultations, consultationId, "deep_validation"],
  url: (consultationId: string) => getApiConsultationDeepValidationUrl(consultationId),
};

export const consultationV2UploadQueryParts = {
  key: (consultationId: string) => [Suffixes.Consultations, consultationId, "upload"],
  url: (consultationId: string) => getApiConsultationUploadUrl(consultationId),
};