import { buildQuery } from "../../queryClient";
import {
  consultationQueryParts,
  consultationsQueryParts,
  consultationsV2QueryParts,
} from "./parts";
import type {
  ConsultationsGetResponse,
  ConsultationsV2GetResponse,
  ConsultationV2CreateResponse,
  UpdateConsultationBody,
} from "./types";

export function buildConsultationsGetQuery() {
  return buildQuery<ConsultationsGetResponse>(consultationsQueryParts.url(), {
    key: consultationsQueryParts.key(),
  });
}

export function buildConsultationsV2GetQuery() {
  return buildQuery<ConsultationsV2GetResponse>(
    consultationsV2QueryParts.url(),
    { key: consultationsV2QueryParts.key() },
  );
}

export function buildConsultationV2CreateQuery(
  onSuccess: (data: ConsultationV2CreateResponse) => Promise<void>,
) {
  return buildQuery<ConsultationV2CreateResponse>(
    consultationsV2QueryParts.url(),
    {
      key: [...consultationsV2QueryParts.key(), "create"],
      method: "POST",
      errorMessage: "Failed to create consultation",
      onSuccess: (data) => onSuccess(data as ConsultationV2CreateResponse),
    },
  );
}

export function buildConsultationDeleteQuery(consultationId: string) {
  return buildQuery<void>(consultationQueryParts.url(consultationId), {
    key: consultationQueryParts.key(consultationId),
    method: "DELETE",
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
