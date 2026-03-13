import type { GeneratedTheme as CandidateTheme } from "../../types";

export type CandidateThemesGetResponse = {
  count: number;
  next: string | null;
  previous: string | null;
  results: CandidateTheme[];
};