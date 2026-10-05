import type { Consultation, ConsultationStage, RunningJob } from "../../types";

export type ConsultationsGetResponse = {
  count: number;
  next: string | null;
  previous: string | null;
  results: Consultation[];
};
export type ConsultationV2User = {
  id: number;
  email: string;
  is_staff: boolean;
};
export type ConsultationV2 = {
  id: string;
  title: string;
  code: string;
  stage: ConsultationStage | "setup" | "finding_themes";
  data_source: "qualtrics" | "citizen-space" | null;
  users: ConsultationV2User[];
  created_by: ConsultationV2User | null;
  created_at: string;
  started_at: string | null;
  closed_at: string | null;
  is_owner: boolean | null;
  is_assigned: boolean;
  running_job: RunningJob;
};
export type ConsultationsV2GetResponse = {
  count: number;
  next: string | null;
  previous: string | null;
  results: ConsultationV2[];
};
export type ConsultationV2CreateResponse = {
  id: string;
  title: string;
};
export type UpdateConsultationBody = {
  stage?: ConsultationStage;
};
