import { getApiConsultationUrl, Routes, Suffixes } from "../routes";
import type { Consultation } from "../types";

// ============================================================
// Query Keys and API URLs
// ============================================================

export const consultations = {
  list: {
    key: () => Suffixes.Consultations as const,
    url: () => Routes.ApiConsultations,
  },
  detail: {
    key: (consultationId: string) => [Suffixes.Consultations, consultationId] as const,
    url: (consultationId: string) => getApiConsultationUrl(consultationId),
  },
};

// ============================================================
// Query Options
// ============================================================

export type ListConsultationsResponse = {
  count: number;
  next: string | null;
  previous: string | null;
  results: Consultation[];
};

export const listConsultationsQueryOptions = () => ({
  queryKey: consultations.list.key(),
  queryFn: async (): Promise<ListConsultationsResponse> => {
    const response = await fetch(consultations.list.url());
    if (!response.ok) throw new Error("Failed to fetch consultations");
    return response.json();
  },
});

export const detailConsultationQueryOptions = (consultationId: string) => ({
  queryKey: consultations.detail.key(consultationId),
  queryFn: async (): Promise<Consultation> => {
    const response = await fetch(consultations.detail.url(consultationId));
    if (!response.ok)
      throw new Error(`Failed to fetch consultation: ${consultationId}`);
    return response.json();
  },
});

// ============================================================
// Mutation Functions
// ============================================================

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