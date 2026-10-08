import type { Consultation, ConsultationStage, User } from "../../types";

export type ConsultationsGetResponse = {
  count: number;
  next: string | null;
  previous: string | null;
  results: Consultation[];
};
export type ConsultationV2User = Pick<User, "id" | "email" | "is_staff">;
export type ConsultationV2 = Omit<Consultation, "created_by"> & {
  data_source: "qualtrics" | "citizen-space" | null;
  users: ConsultationV2User[];
  created_by: ConsultationV2User | null;
  started_at: string | null;
  closed_at: string | null;
  is_owner: boolean | null;
  is_assigned: boolean;
};
export type ConsultationsV2GetResponse = Omit<
  ConsultationsGetResponse,
  "results"
> & { results: ConsultationV2[] };
export type ConsultationV2CreateResponse = Pick<ConsultationV2, "id" | "title">;
export type UpdateConsultationBody = {
  stage?: ConsultationStage;
};
