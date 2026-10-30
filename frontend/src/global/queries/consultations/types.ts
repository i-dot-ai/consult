import type { Consultation, ConsultationStage, User } from "../../types";

export type ConsultationsGetResponse = {
  count: number;
  next: string | null;
  previous: string | null;
  results: Consultation[];
};
export type ConsultationV2User = Pick<User, "id" | "email" | "is_staff">;
export type DataSource = "qualtrics" | "citizen-space";
// order of import statuses is significant
export const surveyImportStatuses = [
  "not_started",
  "viewed_overview",
  "viewed_provider",
  "viewed_checklist",
  "viewed_upload",
  "file_uploading",
  "pending_questions",
  "pending_demographics",
  "import_failed",
  "import_complete",
] as const;
export type SurveyImportStatus = (typeof surveyImportStatuses)[number];

export type ConsultationV2 = Omit<Consultation, "created_by"> & {
  data_source: DataSource | null;
  users: ConsultationV2User[];
  created_by: ConsultationV2User | null;
  started_at: string | null;
  closed_at: string | null;
  is_owner: boolean | null;
  is_assigned: boolean;
  survey_import_status: SurveyImportStatus;
};
export type ConsultationsV2GetResponse = Omit<
  ConsultationsGetResponse,
  "results"
> & { results: ConsultationV2[] };
export type ConsultationV2CreateResponse = Pick<ConsultationV2, "id" | "title">;
export type ConsultationV2UpdateBody = {
  title?: string;
  data_source?: DataSource | null;
};
export type ConsultationV2UpdateResponse = Pick<
  ConsultationV2,
  "id" | "title" | "data_source"
>;
export type UpdateConsultationBody = {
  stage?: ConsultationStage;
};
