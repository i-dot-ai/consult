import urlJoin from "url-join";

import {
  getApiConsultationsRootUrl,
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
  url: (consultationId: string) =>
    urlJoin(getApiConsultationsRootUrl(), consultationId, "/"),
};
