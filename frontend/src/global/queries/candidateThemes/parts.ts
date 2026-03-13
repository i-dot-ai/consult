import { getApiGetGeneratedThemesUrl, getApiSelectGeneratedThemeUrl, Suffixes } from "../../routes";

export const candidateThemesGetQueryParts = {
  key: (consultationId: string, questionId: string) =>
    [Suffixes.CandidateThemes, consultationId, questionId],
  url: (consultationId: string, questionId: string) =>
    getApiGetGeneratedThemesUrl(consultationId, questionId),
}
export const candidateThemesSelectQueryParts = {
  key: (consultationId: string, questionId: string, candidateThemeId: string) =>
    [Suffixes.CandidateThemes, consultationId, questionId, candidateThemeId],
  url: (
    consultationId: string,
    questionId: string,
    candidateThemeId: string,
  ) =>
    getApiSelectGeneratedThemeUrl(
      consultationId,
      questionId,
      candidateThemeId,
    ),
}
