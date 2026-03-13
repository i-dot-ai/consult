import { getApiGetSelectedThemesUrl, getApiGetSelectedThemeUrl, Suffixes } from "../../routes"

export const selectedThemesQueryParts = {
  key: (consultationId: string, questionId: string) => [
    Suffixes.SelectedThemes,
    consultationId,
    questionId,
  ],
  url: (consultationId: string, questionId: string) =>
    getApiGetSelectedThemesUrl(consultationId, questionId),
}

export const selectedThemeQueryParts = {
  key: (selectedThemeId: string) =>
      [Suffixes.SelectedThemes, selectedThemeId] as const,
  url: (consultationId: string, questionId: string, themeId: string) =>
    getApiGetSelectedThemeUrl(consultationId, questionId, themeId),
}
