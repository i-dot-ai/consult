import {
  getApiAnswersUrl,
  getApiQuestionResponsesUrl,
  Suffixes,
} from "../routes";
import type { ResponsesBody } from "../types";

const SAMPLE_ANSWER_COUNT = 3;

export async function fetchSampleAnswers(
  consultationId: string,
  questionId: string,
): Promise<string[]> {
  const url = `${getApiQuestionResponsesUrl(consultationId, questionId)}?page_size=${SAMPLE_ANSWER_COUNT}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(
      `Failed to fetch sample answers for question ${questionId}`,
    );
  }
  const data = await response.json();
  const respondents: { free_text_answer_text: string }[] =
    data.all_respondents ?? [];
  return respondents.map((respondent) => respondent.free_text_answer_text);
}

// ============================================================
// Query Keys and API URLs
// ============================================================

export const responses = {
  list: {
    key: (consultationId: string) =>
      [Suffixes.Responses, consultationId] as const,
    url: (consultationId: string) => getApiAnswersUrl(consultationId),
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
  queryFn: async (): Promise<ResponsesBody[]> => {
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
