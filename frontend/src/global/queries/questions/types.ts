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
export type DemographicMergeBody = {
  new_value: string;
  responses: string[];
};
