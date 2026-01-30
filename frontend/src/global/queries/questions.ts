import type { Question } from "../types";
export type { Question } from "../types";
import { apiUrl, CONSULTATIONS, QUESTIONS } from "./resources";

// ============================================================
// Routes and Keys
// ============================================================

export const questions = {
  list: {
    key: (consultationId: string) => [QUESTIONS, consultationId] as const,
    url: (consultationId: string) =>
      apiUrl(CONSULTATIONS, consultationId, QUESTIONS),
  },
  detail: {
    key: (questionId: string) => [QUESTIONS, questionId] as const,
    url: (consultationId: string, questionId: string) =>
      apiUrl(CONSULTATIONS, consultationId, QUESTIONS, questionId),
  },
};

// ============================================================
// Query Options
// ============================================================

export type ListQuestionsResponse = {
  count: number;
  next: string | null;
  previous: string | null;
  results: Question[];
};

export const listQuestionsQueryOptions = (consultationId: string) => ({
  queryKey: questions.list.key(consultationId),
  queryFn: async (): Promise<ListQuestionsResponse> => {
    const response = await fetch(questions.list.url(consultationId));
    if (!response.ok) throw new Error("Failed to fetch questions");
    return response.json();
  },
});

export const detailQuestionQueryOptions = (
  consultationId: string,
  questionId: string,
) => ({
  queryKey: questions.detail.key(questionId),
  queryFn: async (): Promise<Question> => {
    const response = await fetch(
      questions.detail.url(consultationId, questionId),
    );
    if (!response.ok)
      throw new Error(`Failed to fetch question: ${questionId}`);
    return response.json();
  },
});

// ============================================================
// Mutation Functions
// ============================================================

export type UpdateQuestionBody = {
  theme_status?: "confirmed" | "pending";
};

export const updateQuestion = async (
  consultationId: string,
  questionId: string,
  body: UpdateQuestionBody,
): Promise<Question> => {
  const response = await fetch(
    questions.detail.url(consultationId, questionId),
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    },
  );
  if (!response.ok) throw new Error(`Failed to update question: ${questionId}`);
  return response.json();
};
