export type QuestionType = "demographic" | "closed" | "open";
export type DashboardRole = "filter" | "standalone";
export type QuestionV2 = {
  id: string;
  number: number;
  text: string;
  type: QuestionType | null;
  closed_question: string | null;
  short_name: string;
  dashboard_role: DashboardRole;
  status: "draft" | "configured" | "finalising_themes" | "confirmed";
  response_count: number;
};
export type QuestionV2UpdateBody = {
  text?: string;
  type?: QuestionType | null;
  closed_question?: string | null;
  short_name?: string;
  dashboard_role?: DashboardRole;
};
export type DemographicAnswer = {
  text: string;
  count: number;
  responses: string[];
};

// Dashboard question-detail payload: QuestionV2 plus the response counts and
// multi-choice answers the dashboard reads (see QuestionDashboardSerializerV2).
export type QuestionDetailV2 = QuestionV2 & {
  total_response_count: number;
  free_text_response_count: number;
  multi_choice_response_count: number;
  multiple_choice_answer: {
    text: string;
    response_count: number;
  }[];
  proportion_of_audited_answers: number;
  theme_status: string;
};

// v2 show-next payload: type replaces the v1 has_free_text boolean.
export type ShowNextResponseResultV2 = {
  next_response: {
    id: string;
    consultation_id: string;
    question_id: string;
  } | null;
  type: QuestionType | null;
  message: string;
};
export type DemographicMergeBody = {
  new_value: string;
  responses: string[];
};
