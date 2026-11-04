import { buildQuery, type FetchError } from "../../queryClient";
import {
  consultationFindThemesQueryParts,
  consultationQueryParts,
  consultationsQueryParts,
  consultationsV2QueryParts,
  consultationV2AssignUsersQueryParts,
  consultationV2DeepValidationQueryParts,
  consultationV2QueryParts,
  consultationV2UploadQueryParts,
  consultationV2UserQueryParts,
} from "./parts";
import type {
  ConsultationsGetResponse,
  ConsultationsV2GetResponse,
  ConsultationV2,
  ConsultationV2AssignUsersResponse,
  ConsultationV2CreateResponse,
  ConsultationV2UpdateResponse,
  UpdateConsultationBody,
} from "./types";
import type { Consultation } from "../../types";

export function buildConsultationsGetQuery() {
  return buildQuery<ConsultationsGetResponse>(consultationsQueryParts.url(), {
    key: consultationsQueryParts.key(),
  });
}

export function buildConsultationsV2GetQuery() {
  return buildQuery<ConsultationsGetResponse>(consultationsV2QueryParts.url(), {
    key: consultationsV2QueryParts.key(),
  });
}

export function buildConsultationV2CreateQuery(
  onSuccess: (data: ConsultationV2CreateResponse) => Promise<void>,
  onError: (error: FetchError<unknown>) => Promise<void>,
) {
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

export function buildConsultationV2UpdateQuery(
  consultationId: string,
  onSuccess?: (data: ConsultationV2UpdateResponse) => Promise<void>,
  onError?: (error: FetchError<unknown>) => Promise<void>,
) {
  return buildQuery<ConsultationV2UpdateResponse>(
    consultationV2QueryParts.url(consultationId),
    {
      key: [...consultationV2QueryParts.key(consultationId), "update"],
      method: "PATCH",
      errorMessage: "Failed to update consultation",
      onSuccess: async (data) => {
        await onSuccess?.(data as ConsultationV2UpdateResponse);
      },
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
  return buildQuery<ConsultationV2>(
    consultationQueryParts.url(consultationId),
    {
      key: consultationQueryParts.key(consultationId),
    },
  );
}

export function buildConsultationRenameQuery(consultationId: string) {
  return buildQuery<Consultation>(consultationQueryParts.url(consultationId), {
    key: [...consultationQueryParts.key(consultationId), "patch"],
    method: "PATCH",
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
  const params = new URLSearchParams({ title__iexact: title });

  return buildQuery<ConsultationsV2GetResponse>(
    `${consultationsV2QueryParts.url()}?${params.toString()}`,
    {
      key: [...consultationsV2QueryParts.key(), "title", title],
      errorMessage: "Failed to look up consultation",
    },
  );
}

export function buildConsultationDeepValidationQuery(
  consultationId: string,
  onError?: () => Promise<void>,
) {
  return buildQuery<Consultation>(
    consultationV2DeepValidationQueryParts.url(consultationId),
    {
      key: [...consultationV2DeepValidationQueryParts.key(consultationId)],
      method: "POST",
      stringifyBody: false,
      omitContentType: true,
      onError: onError,
    },
  );
}

export function buildConsultationUploadQuery(
  consultationId: string,
  onError?: () => Promise<void>,
) {
  return buildQuery<Consultation>(
    consultationV2UploadQueryParts.url(consultationId),
    {
      key: [...consultationV2UploadQueryParts.key(consultationId)],
      method: "POST",
      stringifyBody: false,
      omitContentType: true,
      onError: onError,
    },
  );
}

export function buildConsultationV2GetQuery(consultationId: string) {
  return buildQuery<ConsultationV2>(
    consultationV2QueryParts.url(consultationId),
    {
      key: consultationV2QueryParts.key(consultationId),
      errorMessage: "Failed to load consultation",
    },
  );
}

export function buildConsultationV2AssignUsersQuery(consultationId: string) {
  return buildQuery<ConsultationV2AssignUsersResponse>(
    consultationV2AssignUsersQueryParts.url(consultationId),
    {
      key: consultationV2AssignUsersQueryParts.key(consultationId),
      method: "POST",
      errorMessage: "Failed to add people",
    },
  );
}

export function buildConsultationV2RemoveUserQuery(consultationId: string) {
  return buildQuery<null>(
    consultationV2UserQueryParts.url(consultationId, ":userId"),
    {
      key: consultationV2UserQueryParts.key(consultationId),
      method: "DELETE",
      errorMessage: "Failed to remove a person",
    },
  );
}

export function buildFindingThemesQuery(
  consultationId: string,
  onError?: () => Promise<void>,
) {
  return buildQuery<Consultation>(
    consultationFindThemesQueryParts.url(consultationId),
    {
      key: [...consultationFindThemesQueryParts.key(consultationId)],
      method: "POST",
      onError: onError,
    },
  );
}
