import { buildQuery } from "../queryClient";
import { getApiConsultationUrl, Routes, Suffixes } from "../routes";
import type { Consultation } from "../types";


export type ListConsultationsResponse = {
  count: number;
  next: string | null;
  previous: string | null;
  results: Consultation[];
};

export function buildConsultationsGetQuery() {
  return buildQuery<ListConsultationsResponse>(
    `${Routes.ApiConsultations}?scope=assigned`,
    { key: [Suffixes.Consultations] },
  );
}

export function buildConsultationGetQuery(consultationId: string) {
  return buildQuery<ListConsultationsResponse>(
    getApiConsultationUrl(consultationId),
    { key: [Suffixes.Consultations, consultationId] },
  );
}

// ============================================================
// Query Keys and API URLs
// ============================================================

export const consultations = {
  list: {
    key: () => Suffixes.Consultations as const,
    url: () => Routes.ApiConsultations,
  },
  detail: {
    key: (consultationId: string) =>
      [Suffixes.Consultations, consultationId] as const,
    url: (consultationId: string) => getApiConsultationUrl(consultationId),
  },
};

// ============================================================
// Query Options
// ============================================================

export const detailConsultationQueryOptions = (consultationId: string) => ({
  queryKey: consultations.detail.key(consultationId),
  queryFn: async (): Promise<Consultation> => {
    const response = await fetch(consultations.detail.url(consultationId));
    if (!response.ok)
      throw new Error(`Failed to fetch consultation: ${consultationId}`);
    return response.json();
  },
});

export type UpdateConsultationBody = {
  stage?: "theme_sign_off" | "theme_mapping" | "analysis";
};

export const updateConsultation = async (
  consultationId: string,
  body: UpdateConsultationBody,
): Promise<void> => {
  const response = await fetch(consultations.detail.url(consultationId), {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok)
    throw new Error(`Failed to update consultation: ${consultationId}`);
};
