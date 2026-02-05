import type { SvelteURLSearchParams } from "svelte/reactivity";

export interface NavItem {
  text: string;
  url: string;
}

export interface QuestionMultiAnswer {
  id: string;
  text: string;
  response_count: number;
}

export interface Question {
  id?: string;
  number?: number;
  total_responses?: number;
  question_text?: string;
  has_free_text?: boolean;
  has_multiple_choice?: boolean;
  multiple_choice_answer?: QuestionMultiAnswer[];
  proportion_of_audited_answers?: number;
  theme_status?: string;
}

export type ConsultationStage = "theme_sign_off" | "theme_mapping" | "analysis";
export interface NextResponseInfo {
  id: string;
  consultation_id: string;
  question_id: string;
}

export interface ShowNextResponseResult {
  next_response: NextResponseInfo | null;
  has_free_text: boolean;
  message: string;
}

export interface Consultation {
  id: string;
  title: string;
  code: string;
  stage: "theme_sign_off" | "theme_mapping" | "analysis";
  created_at: string;
}

export interface ConsultationFolder {
  id: string;
  title: string;
  code: string;
}

export interface Respondent {
  id: string;
  consultation: string;
  themefinder_id: number;
  demographics: RespondentDemoItem[];
  name?: string;
}

export interface RespondentDemoItem {
  name: string;
  value: string;
}

export interface FormattedTheme {
  id: string;
  name: string;
  description: string;
  count: number;
  highlighted?: boolean;
  handleClick?: (e: MouseEvent) => void;
  key?: string;
}

export interface SelectOption {
  value: string;
  label: string;
}

export interface RadioItem {
  value: string;
  text: string;
  checked?: boolean;
  disabled?: boolean;
}

export interface CheckboxItem {
  value: string;
  text: string;
  hint?: string;
  disabled?: boolean;
}

export enum SearchModeValues {
  SEMANTIC = "semantic",
  KEYWORD = "keyword",
}
export enum SearchModeLabels {
  SEMANTIC = "Semantic",
  KEYWORD = "Keyword",
}
export enum TitleLevels {
  One = 1,
  Two = 2,
  Three = 3,
  Four = 4,
  Five = 5,
  Six = 6,
}

export enum TabNames {
  QuestionSummary = "tab-question-summary",
  ResponseAnalysis = "tab-response-analysis",
}

export enum TabDirections {
  Forward = "forward",
  Backward = "backward",
}

export interface SearchableSelectOption<T> {
  value: T;
  label: string;
  description?: string;
  disabled?: boolean;
}

export interface ResponseTheme {
  id: string;
  name: string;
  description: string;
  key?: string;
}

export interface ResponseThemeInformation {
  all_themes: ResponseTheme[];
  selected_themes: ResponseTheme[];
}

export interface QuestionResponseResponse {
  id: string;
  respondent: Respondent;
  question: Question;
  free_text_answer_text: string;
  chosen_options: MultiChoiceResponse;
  created_at: string;
  modified_at: string;
  // Extra fields not mapped:
  // embedding: string;
  // searchVector: string;
}

export interface ResponseAnswer {
  id: string;
  identifier: number; // respondent themefinder id
  question_id: string;
  respondent_id: string;
  free_text_answer_text: string;
  demographic_data: { [category: string]: string };
  themes: ResponseTheme[] | null;
  multiple_choice_answer: string[];
  evidenceRich: boolean;
  sentiment: string | null;
  human_reviewed: boolean;
  is_flagged: boolean;
  is_edited?: boolean;
  is_read: boolean;
}

export interface DemoOption {
  [category: string]: string[];
}

export interface DemoData {
  [category: string]: { [rowKey: string]: number };
}

export interface DemoTotalCounts {
  [category: string]: number;
}
export interface ThemeAggr {
  [id: string]: number;
}

export interface ConsultationResponse {
  id: string;
  title: string;
  code: string;
  users: User[];
  stage: "theme_sign_off" | "theme_mapping" | "analysis";
}
export interface QuestionsResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Question[];
}
export interface SelectedThemesResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: SelectedTheme[];
}
export interface SelectedThemesDeleteResponse {
  last_modified_by?: { email: string };
  latest_version?: string;
}
export interface GeneratedThemesResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: GeneratedTheme[];
}
export interface AnswersResponse {
  respondents_total: number;
  filtered_total: number;
  has_more_pages: boolean;
  all_respondents: ResponseAnswer[];
}
export interface RespondentsResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Respondent[];
}

export interface ThemeInfoResponse {
  themes: ResponseTheme[];
}

export interface DemoAggrResponse {
  demographic_aggregations: DemoData;
}

export interface ThemeAggrResponse {
  theme_aggregations: ThemeAggr;
}

export interface MultiChoiceResponseItem {
  answer: string;
  response_count: number;
}
export type MultiChoiceResponse = MultiChoiceResponseItem[];

export interface DemoOptionsResponseItem {
  id: string;
  name: string;
  value: string;
  count: number;
}
export type DemoOptionsResponse = DemoOptionsResponseItem[];

export type User = {
  id: number;
  email: string;
  is_staff: boolean;
  created_at: string;
};

export interface GeneratedTheme {
  id: string;
  name: string;
  description: string;
  selectedtheme_id?: string; // if a selected theme exists based on this one
  children?: GeneratedTheme[]; // recursive list
}
export interface SelectedTheme {
  id: string;
  name: string;
  description: string;
  version: number;
  modified_at: string; // timestamp
  last_modified_by: string; // user id
}

export enum OnboardingKeys {
  prefix = "onboardingComplete",
  themeSignoff = "onboardingComplete-theme-sign-off",
  themeSignoffArchive = "onboardingComplete-theme-sign-off-archive",
}

export type AstroGlobalRuntime = {
  url: {
    pathname: string;
    searchParams: SvelteURLSearchParams;
  };
  params: {
    consultationId?: string;
    questionId?: string;
    userId?: string;
    responseId?: string;
    respondentId?: string;
  };
  redirect: (url: string) => void;
};
