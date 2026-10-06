import {
  getApiConsultationsUrl,
  getApiConsultationUrl,
  Routes,
  Suffixes,
} from "../../routes";

export const consultationsQueryParts = {
  key: () => [Suffixes.Consultations],
  url: () => `${Routes.ApiConsultations}?scope=assigned`,
};

export const consultationsV2QueryParts = {
  key: () => [Suffixes.Consultations, "v2"],
  url: () => getApiConsultationsUrl(),
};

export const consultationQueryParts = {
  key: (consultationId: string) => [Suffixes.Consultations, consultationId],
  url: (consultationId: string) => getApiConsultationUrl(consultationId),
};
