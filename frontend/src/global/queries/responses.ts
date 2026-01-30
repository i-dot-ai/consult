import type { AnswersResponse } from "../types";
export type { AnswersResponse } from "../types";
import { apiUrl, CONSULTATIONS, RESPONSES } from "./resources";

// ============================================================
// Query Keys and API URLs
// ============================================================

export const responses = {
  list: {
    key: (consultationId: string) => [RESPONSES, consultationId] as const,
    url: (consultationId: string) =>
      apiUrl(CONSULTATIONS, consultationId, RESPONSES),
  },
  representativeResponses: {
    key: (variant: string, themeId: string) =>
      ["representativeResponses", variant, themeId] as const,
  },
};

// ============================================================
// Query Options
// ============================================================

export type RepresentativeResponsesParams = {
  consultationId: string;
  questionId: string;
  themeName: string;
  themeDescription: string;
  themeId: string;
  variant: "selected" | "candidate";
};

export const representativeResponsesQueryOptions = ({
  consultationId,
  questionId,
  themeName,
  themeDescription,
  themeId,
  variant,
}: RepresentativeResponsesParams) => ({
  queryKey: responses.representativeResponses.key(variant, themeId),
  queryFn: async (): Promise<AnswersResponse> => {
    const queryString = new URLSearchParams({
      searchMode: "representative",
      searchValue: `${themeName} ${themeDescription}`,
      question_id: questionId,
    }).toString();

    const response = await fetch(
      `${responses.list.url(consultationId)}?${queryString}`,
    );
    if (!response.ok)
      throw new Error(
        `Failed to fetch representative responses for ${variant} theme: ${themeId}`,
      );
    return response.json();
  },
});
