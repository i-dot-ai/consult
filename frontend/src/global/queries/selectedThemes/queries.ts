import type { SelectedTheme } from "../../types";
import type {
  SelectedThemeMutationError,
  UpdateSelectedThemeBody,
} from "./types";
import { selectedThemeQueryParts, selectedThemesQueryParts } from "./parts";

export const detailSelectedThemeQueryOptions = (
  consultationId: string,
  questionId: string,
  selectedThemeId: string,
) => ({
  queryKey: selectedThemeQueryParts.key(selectedThemeId),
  queryFn: async (): Promise<SelectedTheme> => {
    const response = await fetch(
      selectedThemeQueryParts.url(consultationId, questionId, selectedThemeId),
    );
    if (!response.ok)
      throw new Error(`Failed to fetch selected theme: ${selectedThemeId}`);
    return response.json();
  },
});

export const updateSelectedTheme = async (
  consultationId: string,
  questionId: string,
  themeId: string,
  version: number,
  body: UpdateSelectedThemeBody,
): Promise<SelectedTheme> => {
  const response = await fetch(
    selectedThemeQueryParts.url(consultationId, questionId, themeId),
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

export const createSelectedTheme = async (
  consultationId: string,
  questionId: string,
  name: string,
  description: string,
): Promise<void> => {
  const response = await fetch(
    selectedThemesQueryParts.url(consultationId, questionId),
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, description }),
    },
  );
  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    throw { status: response.status, ...errData } as SelectedThemeMutationError;
  }
};

export const deleteSelectedTheme = async (
  consultationId: string,
  questionId: string,
  themeId: string,
  version: number,
): Promise<void> => {
  const response = await fetch(
    selectedThemeQueryParts.url(consultationId, questionId, themeId),
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
