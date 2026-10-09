import { buildQuery, type FetchError } from "../../queryClient";
import { getDataSetupV2Enabled } from "../../utils";
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
import type { Consultation } from "../../types";

export function buildConsultationsGetQuery() {
  return buildQuery<ConsultationsGetResponse>(consultationsQueryParts.url(), {
    key: consultationsQueryParts.key(),
  });
}

export function buildConsultationV2CreateQuery(
  onSuccess: (data: ConsultationV2CreateResponse) => Promise<void>,
  onError: (error: FetchError<unknown>) => Promise<void>,
) {
  if (!getDataSetupV2Enabled()) {
    throw new Error("Creating consultations requires data setup v2");
  }

  return buildQuery<ConsultationV2CreateResponse>(
    consultationsV2QueryParts.url(),
    {
      key: [...consultationsV2QueryParts.key(), "create"],
      method: "POST",
      errorMessage: "Failed to create consultation",
      onSuccess: (data) => onSuccess(data as ConsultationV2CreateResponse),
      onError,
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
  return buildQuery<Consultation>(consultationQueryParts.url(consultationId), {
    key: consultationQueryParts.key(consultationId),
  });
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

export function buildConsultationsV2ByTitleQuery(title: string) {
  if (!getDataSetupV2Enabled()) {
    throw new Error("Looking up consultations by title requires data setup v2");
  }

  const params = new URLSearchParams({ title__iexact: title });

  return buildQuery<ConsultationsV2GetResponse>(
    `${consultationsV2QueryParts.url()}?${params.toString()}`,
    {
      key: [...consultationsV2QueryParts.key(), "title", title],
      errorMessage: "Failed to look up consultation",
    },
  );
}
