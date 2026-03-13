import { buildQuery, type FetchError } from "../../queryClient";
import type {
  SelectedTheme,
  SelectedThemesDeleteResponse,
} from "../../types";
import type { SaveThemeError } from "../../../components/theme-sign-off/ErrorModal/types";
import type {
  errorData,
  SelectedThemeMutationError,
  SelectedThemesGetResponse,
  UpdateSelectedThemeBody
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

export function buildSelectedThemesGetQuery(consultationId: string, questionId: string) {
  return buildQuery<SelectedThemesGetResponse>(
    selectedThemesQueryParts.url(consultationId, questionId),
    {
      key: selectedThemesQueryParts.key(consultationId, questionId),
    },
  );
};

export function buildSelectedThemeCreateQuery(
  consultationId: string,
  questionId: string,
  onSuccess: () => Promise<void>,
) {
  return buildQuery<SelectedThemesGetResponse>(
    selectedThemesQueryParts.url(consultationId, questionId),
    {
      key: selectedThemesQueryParts.key(consultationId, questionId),
      method: "POST",
      onSuccess: onSuccess,
    },
  );
};

export function buildSelectedThemeDeleteQuery(
  consultationId: string,
  questionId: string,
  onSuccess: () => Promise<void>,
  onError: (error: FetchError<errorData>) => Promise<void>,
) {
  return buildQuery<SelectedThemesDeleteResponse>(
    selectedThemeQueryParts.url(consultationId, questionId, ":themeId"),
    {
      key: selectedThemesQueryParts.key(consultationId, questionId),
      method: "DELETE",
      onSuccess: onSuccess,
      onError: onError,
      getVariables: (themeId, version) => {
        return {
          headers: {
            "Content-Type": "application/json",
            "If-Match": version,
          },
          params: {
            themeId: themeId,
          },
        };
      },
    },
  );
};

export const getSelectedThemesDeleteQuery = (
  consultationId: string,
  questionId: string,
  resetQueries: () => void,
  showError: (args: SaveThemeError) => void,
) => {
  const query = buildQuery<SelectedThemesDeleteResponse>(
    selectedThemeQueryParts.url(consultationId, questionId, ":themeId"),
    {
      method: "DELETE",
      onSuccess: async () => {
        resetQueries();
      },
      onError: async (error: FetchError<errorData>) => {
        if (error.status === 404) {
          // SelectedTheme has already been deleted, just refetch
          resetQueries();
        } else if (error.status === 412) {
          showError({
            type: "remove-conflict",
            lastModifiedBy: error.data?.last_modified_by?.email || "",
            latestVersion: error.data?.latest_version || "",
          });
        } else {
          showError({ type: "unexpected" });
          console.error(error);
        }
      },
      getVariables: (themeId, version) => {
        return {
          headers: {
            "Content-Type": "application/json",
            "If-Match": version,
          },
          params: {
            themeId: themeId,
          },
        };
      },
    },
  );

  return query;
};
