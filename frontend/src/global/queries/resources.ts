import urlJoin from "url-join";

export const CANDIDATE_THEMES = "candidate-themes";
export const CONSULTATIONS = "consultations";
export const QUESTIONS = "questions";
export const RESPONSES = "responses";
export const SELECTED_THEMES = "selected-themes";

export const apiUrl = (...segments: string[]) =>
  urlJoin("/api", ...segments, "/");
