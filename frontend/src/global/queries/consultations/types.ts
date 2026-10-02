import type { Consultation, ConsultationStage } from "../../types";

export type ConsultationsGetResponse = {
  count: number;
  next: string | null;
  previous: string | null;
  results: Consultation[];
};
export type ConsultationV2 = {
  id: string;
  title: string;
  created_at: string;
  created_by: { id: number; email: string; is_staff: boolean } | null;
  is_owner: boolean | null;
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
