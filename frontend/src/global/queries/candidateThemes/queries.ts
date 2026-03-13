import { buildQuery } from "../../queryClient";
import type { GeneratedTheme } from "../../types";
import {
  candidateThemesGetQueryParts,
  candidateThemesSelectQueryParts,
} from "./parts";
import type { CandidateThemesGetResponse } from "./types";

export function buildCandidateThemesGetQuery(
  consultationId: string,
  questionId: string,
) {
  return buildQuery<CandidateThemesGetResponse>(
    candidateThemesGetQueryParts.url(consultationId, questionId),
    {
      key: candidateThemesGetQueryParts.key(consultationId, questionId),
    },
  );
}

export function buildCandidateThemeSelectQuery(
  consultationId: string,
  questionId: string,
  candidateThemeId: string,
  onSuccess: (
    data: unknown,
    variables: { params: { themeId: string } },
  ) => Promise<void>,
) {
  return buildQuery<GeneratedTheme>(
    candidateThemesSelectQueryParts.url(
      consultationId,
      questionId,
      candidateThemeId,
    ),
    {
      key: candidateThemesSelectQueryParts.key(
        consultationId,
        questionId,
        candidateThemeId,
      ),
      method: "POST",
      onSuccess: onSuccess,
      getVariables: (themeId) => ({
        params: {
          themeId: themeId,
        },
      }),
    },
  );
}
