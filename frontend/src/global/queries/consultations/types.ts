import type { Consultation, ConsultationStage } from "../../types";

export type ConsultationsGetResponse = {
  count: number;
  next: string | null;
  previous: string | null;
  results: Consultation[];
};
export type UpdateConsultationBody = {
  stage?: ConsultationStage;
};
