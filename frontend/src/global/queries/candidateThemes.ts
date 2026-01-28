import type { GeneratedTheme as CandidateTheme } from "../types";
export type { GeneratedTheme as CandidateTheme } from "../types";
import {
  apiUrl,
  CANDIDATE_THEMES,
  CONSULTATIONS,
  QUESTIONS,
} from "./resources";

// ============================================================
// Query Keys and API URLs
// ============================================================

export const candidateThemes = {
  list: {
    key: (consultationId: string, questionId: string) =>
      [CANDIDATE_THEMES, consultationId, questionId] as const,
    url: (consultationId: string, questionId: string) =>
      apiUrl(
        CONSULTATIONS,
        consultationId,
        QUESTIONS,
        questionId,
        CANDIDATE_THEMES,
      ),
  },
  select: {
    url: (
      consultationId: string,
      questionId: string,
      candidateThemeId: string,
    ) =>
      apiUrl(
        CONSULTATIONS,
        consultationId,
        QUESTIONS,
        questionId,
        CANDIDATE_THEMES,
        candidateThemeId,
        "select",
      ),
  },
};

// ============================================================
// Query Options
// ============================================================

export type ListCandidateThemesResponse = {
  count: number;
  next: string | null;
  previous: string | null;
  results: CandidateTheme[];
};

export const listCandidateThemesQueryOptions = (
  consultationId: string,
  questionId: string,
) => ({
  queryKey: candidateThemes.list.key(consultationId, questionId),
  queryFn: async (): Promise<ListCandidateThemesResponse> => {
    const response = await fetch(
      candidateThemes.list.url(consultationId, questionId),
    );
    if (!response.ok) throw new Error("Failed to fetch candidate themes");
    return response.json();
  },
});

// ============================================================
// Mutation Functions
// ============================================================

export const selectCandidateTheme = async (
  consultationId: string,
  questionId: string,
  candidateThemeId: string,
): Promise<{ id: string }> => {
  const response = await fetch(
    candidateThemes.select.url(consultationId, questionId, candidateThemeId),
    { method: "POST" },
  );
  if (!response.ok) throw new Error("Failed to select candidate theme");
  return response.json();
};
