import { buildQuery } from "../../queryClient";
import { consultationQueryParts, consultationsQueryParts } from "./parts";
import type { ConsultationsGetResponse, UpdateConsultationBody } from "./types";

export function buildConsultationsGetQuery() {
  return buildQuery<ConsultationsGetResponse>(consultationsQueryParts.url(), {
    key: consultationsQueryParts.key(),
  });
}

export function buildConsultationGetQuery(consultationId: string) {
  return buildQuery<ConsultationsGetResponse>(
    consultationQueryParts.url(consultationId),
    { key: consultationQueryParts.key(consultationId) },
  );
}

export const updateConsultation = async (
  consultationId: string,
  body: UpdateConsultationBody,
): Promise<void> => {
  const response = await fetch(consultationQueryParts.url(consultationId), {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok)
    throw new Error(`Failed to update consultation: ${consultationId}`);
};
