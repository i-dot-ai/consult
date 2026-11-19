import { buildQuery } from "../../queryClient";
import {
  demographicAnswersQueryParts,
  demographicMergeQueryParts,
  questionsV2QueryParts,
  questionV2QueryParts,
} from "./parts";
import type {
  DemographicAnswer,
  DemographicMergeBody,
  QuestionDetailV2,
  QuestionV2,
  QuestionV2UpdateBody,
} from "./types";
import type { Question } from "../../types";

export function buildQuestionsV2Query(consultationId: string) {
  return buildQuery<QuestionV2[]>(questionsV2QueryParts.url(consultationId), {
    key: questionsV2QueryParts.key(consultationId),
    errorMessage: "Failed to fetch questions",
  });
}

export function buildQuestionV2UpdateQuery(
  consultationId: string,
  onSuccess?: (data: QuestionV2) => Promise<void>,
) {
  return buildQuery<QuestionV2>(
    questionV2QueryParts.url(consultationId, ":questionId"),
    {
      key: [...questionsV2QueryParts.key(consultationId), "update"],
      method: "PATCH",
      errorMessage: "Failed to update question",
      onSuccess: async (data) => {
        await onSuccess?.(data as QuestionV2);
      },
      getVariables: (questionId, body) => ({
        params: { questionId: questionId as string },
        body: body as QuestionV2UpdateBody,
      }),
    },
  );
}

export async function fetchDemographicAnswers(
  consultationId: string,
  questionId: string,
): Promise<DemographicAnswer[]> {
  const response = await fetch(
    demographicAnswersQueryParts.url(consultationId, questionId),
  );
  if (!response.ok) {
    throw new Error(`Failed to fetch answers for question ${questionId}`);
  }
  return response.json();
}

export function buildDemographicMergeQuery(consultationId: string) {
  return buildQuery<DemographicMergeBody>(
    demographicMergeQueryParts.url(consultationId, ":questionId"),
    {
      key: demographicMergeQueryParts.key(consultationId),
      method: "POST",
      errorMessage: "Failed to merge answers",
      getVariables: (questionId, body) => ({
        params: { questionId: questionId as string },
        body: body as DemographicMergeBody,
      }),
    },
  );
}

/**
 * Dashboard question surfaces exclude demographic-type questions: they exist to
 * back filters, not as analyst-reviewable questions. Legacy v1 payloads carry
 * no `type` and pass through.
 */
export function excludeDemographicQuestions(
  questions: Array<Question | QuestionDetailV2>,
): Array<Question | QuestionDetailV2> {
  return questions.filter(
    (question) => !("type" in question) || question.type !== "demographic",
  );
}
