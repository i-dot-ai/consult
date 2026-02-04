import type { SaveThemeError } from "../../components/theme-sign-off/question/selected-themes/ErrorSavingTheme/ErrorSavingTheme.svelte";
import { buildQuery, FetchError } from "../queryClient";
import type { SelectedTheme, SelectedThemesDeleteResponse, SelectedThemesResponse } from "../types";
export type { SelectedTheme } from "../types";
import { apiUrl, CONSULTATIONS, QUESTIONS, SELECTED_THEMES } from "./resources";

// ============================================================
// Query Keys and API URLs
// ============================================================

export const selectedThemes = {
  list: {
    key: (consultationId: string, questionId: string) =>
      [SELECTED_THEMES, consultationId, questionId],
    url: (consultationId: string, questionId: string) =>
      apiUrl(
        CONSULTATIONS,
        consultationId,
        QUESTIONS,
        questionId,
        SELECTED_THEMES,
      ),
  },
  detail: {
    key: (selectedThemeId: string) =>
      [SELECTED_THEMES, selectedThemeId] as const,
    url: (consultationId: string, questionId: string, themeId: string) =>
      apiUrl(
        CONSULTATIONS,
        consultationId,
        QUESTIONS,
        questionId,
        SELECTED_THEMES,
        themeId,
      ),
  },
};

// ============================================================
// Query Options
// ============================================================

export type ListSelectedThemesResponse = {
  count: number;
  next: string | null;
  previous: string | null;
  results: SelectedTheme[];
};

export const listSelectedThemesQueryOptions = (
  consultationId: string,
  questionId: string,
) => ({
  queryKey: selectedThemes.list.key(consultationId, questionId),
  queryFn: async (): Promise<ListSelectedThemesResponse> => {
    const response = await fetch(
      selectedThemes.list.url(consultationId, questionId),
    );
    if (!response.ok) throw new Error("Failed to fetch selected themes");
    return response.json();
  },
});

export const detailSelectedThemeQueryOptions = (
  consultationId: string,
  questionId: string,
  selectedThemeId: string,
) => ({
  queryKey: selectedThemes.detail.key(selectedThemeId),
  queryFn: async (): Promise<SelectedTheme> => {
    const response = await fetch(
      selectedThemes.detail.url(consultationId, questionId, selectedThemeId),
    );
    if (!response.ok)
      throw new Error(`Failed to fetch selected theme: ${selectedThemeId}`);
    return response.json();
  },
});

// ============================================================
// Mutation Functions
// ============================================================

export type CreateSelectedThemeBody = {
  name: string;
  description: string;
};

export const createSelectedTheme = async (
  consultationId: string,
  questionId: string,
  body: CreateSelectedThemeBody,
): Promise<SelectedTheme> => {
  const response = await fetch(
    selectedThemes.list.url(consultationId, questionId),
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    },
  );
  if (!response.ok) throw new Error("Failed to create theme");
  return response.json();
};

export type UpdateSelectedThemeBody = {
  name: string;
  description: string;
};

export type SelectedThemeMutationError = {
  status: number;
  last_modified_by?: { email: string };
  latest_version?: string;
};

export const updateSelectedTheme = async (
  consultationId: string,
  questionId: string,
  themeId: string,
  version: number,
  body: UpdateSelectedThemeBody,
): Promise<SelectedTheme> => {
  const response = await fetch(
    selectedThemes.detail.url(consultationId, questionId, themeId),
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        "If-Match": String(version),
      },
      body: JSON.stringify(body),
    },
  );
  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    throw { status: response.status, ...errData } as SelectedThemeMutationError;
  }
  return response.json();
};

export const deleteSelectedTheme = async (
  consultationId: string,
  questionId: string,
  themeId: string,
  version: number,
): Promise<void> => {
  const response = await fetch(
    selectedThemes.detail.url(consultationId, questionId, themeId),
    {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
        "If-Match": String(version),
      },
    },
  );
  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    throw { status: response.status, ...errData } as SelectedThemeMutationError;
  }
};


export const getSelectedThemesListQuery = (
  consultationId: string,
  questionId: string
) => {
  return buildQuery<SelectedThemesResponse>(
    selectedThemes.list.url(consultationId, questionId),
    {
      key: selectedThemes.list.key(consultationId, questionId),
    }
  )
}

export const getSelectedThemesDeleteQuery = (
  consultationId: string,
  questionId: string,
  resetQueries: () => void,
  showError: (args: SaveThemeError) => void,
) => {
  const query = buildQuery<SelectedThemesDeleteResponse>(
    selectedThemes.detail.url(consultationId, questionId, ":themeId"),
    {
      method: "DELETE",
      onSuccess: async () => {
        resetQueries();
      },
      onError: async (error: FetchError) => {
        if (error.status === 404) {
          // SelectedTheme has already been deleted, just refetch
          resetQueries();
        } else if (error.status === 412) {
          showError({
            type: "remove-conflict",
            lastModifiedBy:  error.data?.last_modified_by?.email || "",
            latestVersion: error.data?.latest_version || "",
          });
        } else {
          showError({ type: "unexpected" });
          console.error(error);
        }
      },
      getVariables: (themeId: string, version: string) => {
        return ({
          headers: {
            "Content-Type": "application/json",
            "If-Match": version,
          },
          params: {
            "themeId": themeId,
          },
        });
      }
    }
  );

  return query;
}
