import {
  consultationV2AssignUsersQueryParts,
  consultationV2QueryParts,
  consultationV2UserQueryParts,
} from "../../../global/queries/consultations/parts";
import type { ConsultationV2 } from "../../../global/queries/consultations/types";
import { currentUserGetQueryParts } from "../../../global/queries/users/parts";
import type { CurrentUserGetResponse } from "../../../global/queries/users/types";
import type { User } from "../../../global/types";

export const CONSULTATION_ID = "95ab7567-9381-48eb-8d20-ddeb43691b58";
export const CONSULTATION_TITLE = "Future homes standard";

const JOINED_AT = "2026-08-18T09:00:00Z";

export const CREATOR: User = {
  id: 1,
  email: "priya.raghunathan@example.gov.uk",
  is_staff: false,
  created_at: JOINED_AT,
};
export const YOU: User = {
  id: 2,
  email: "f.fisher@example.gov.uk",
  is_staff: false,
  created_at: JOINED_AT,
};
export const COLLEAGUE: User = {
  id: 3,
  email: "sam.kaur@example.gov.uk",
  is_staff: false,
  created_at: JOINED_AT,
};
export const MANY_PEOPLE: User[] = [...Array(11).keys()].map((index) => ({
  id: 10 + index,
  email: `person${index + 1}@example.gov.uk`,
  is_staff: false,
  created_at: JOINED_AT,
}));

export const CURRENT_USER: CurrentUserGetResponse = {
  ...YOU,
};
export const STAFF_USER: CurrentUserGetResponse = {
  ...CURRENT_USER,
  is_staff: true,
};

function consultation(overrides: Partial<ConsultationV2>): ConsultationV2 {
  return {
    id: CONSULTATION_ID,
    title: CONSULTATION_TITLE,
    code: "",
    stage: "setup",
    created_at: JOINED_AT,
    running_job: null,
    data_source: null,
    survey_import_status: "not_started",
    users: [COLLEAGUE, YOU, CREATOR],
    created_by: CREATOR,
    started_at: null,
    closed_at: null,
    is_owner: false,
    is_assigned: true,
    ...overrides,
  };
}

export const INVITED_CONSULTATION = consultation({});
export const OWNED_CONSULTATION = consultation({
  created_by: YOU,
  is_owner: true,
});
export const MANY_PEOPLE_CONSULTATION = consultation({
  created_by: YOU,
  is_owner: true,
  users: [YOU, ...MANY_PEOPLE],
});

export const userMock = {
  url: currentUserGetQueryParts.url(),
  body: CURRENT_USER,
};
export const staffUserMock = {
  url: currentUserGetQueryParts.url(),
  body: STAFF_USER,
};

export const invitedConsultationMock = {
  url: consultationV2QueryParts.url(CONSULTATION_ID),
  body: INVITED_CONSULTATION,
};
export const ownedConsultationMock = {
  url: consultationV2QueryParts.url(CONSULTATION_ID),
  body: OWNED_CONSULTATION,
};
export const manyPeopleConsultationMock = {
  url: consultationV2QueryParts.url(CONSULTATION_ID),
  body: MANY_PEOPLE_CONSULTATION,
};
export const consultationErrorMock = {
  url: consultationV2QueryParts.url(CONSULTATION_ID),
  status: 500,
  body: {},
};

export const userAssignmentMock = {
  url: consultationV2AssignUsersQueryParts.url(CONSULTATION_ID),
  method: "POST",
  body: { added_count: 2 },
};
export const userAssignmentErrorMock = {
  ...userAssignmentMock,
  status: 500,
  body: {},
};

export const userRemovalMock = (userId: number) => ({
  url: consultationV2UserQueryParts.url(CONSULTATION_ID, String(userId)),
  method: "DELETE",
  status: 204,
  body: undefined,
});
export const userRemovalErrorMock = (userId: number) => ({
  ...userRemovalMock(userId),
  status: 500,
  body: {},
});
