import type { Consultation } from "../../types";

export type ConsultationsGetResponse = {
  count: number;
  next: string | null;
  previous: string | null;
  results: Consultation[];
};
export type UpdateConsultationBody = {
  stage?: "theme_sign_off" | "theme_mapping" | "analysis";
};
