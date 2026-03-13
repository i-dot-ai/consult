import type { SelectedTheme } from "../../types";

export type CreateSelectedThemeBody = {
  name: string;
  description: string;
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

export type SelectedThemesGetResponse = {
  count: number;
  next: string | null;
  previous: string | null;
  results: SelectedTheme[];
};

export type errorData = {
  last_modified_by: {
    email?: string;
  };
  latest_version: string;
};