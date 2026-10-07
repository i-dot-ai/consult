import { consultationQueryParts } from "../../../global/queries/consultations/parts";
import { currentUserGetQueryParts } from "../../../global/queries/users/parts";

export const CONSULTATION_ID = "test-consultation";
export const USER_EMAIL = "test@email.com";

const CONSULTAITON_URL = consultationQueryParts.url(CONSULTATION_ID);
const CONSULTATION = {
  id: "95ab7567-9381-48eb-8d20-ddeb43691b58",
  title: "Dummy Consultation at Analysis Stage",
  code: "",
  stage: "analysis",
  users: [
    {
      id: 1,
      email: "admin@example.com",
      is_staff: true,
      created_at: "2026-01-29T14:15:50.850685Z",
    },
  ],
  created_at: "2026-01-29T14:23:14.719743Z",
};

const USER_URL = currentUserGetQueryParts.url();
const USER = {
    "id": 1,
    "email": USER_EMAIL,
    "is_staff": true,
    "created_at": "2026-07-15T08:42:02.852525+01:00"
};

export const defaultMock = {
  url: CONSULTAITON_URL,
  body: CONSULTATION,
};
export const stageFinaliseThemesMock = {
    url: CONSULTAITON_URL,
    body: {
        ...CONSULTATION,
        stage: "finalising_themes",
    },
}

export const multipleUsersMock = {
    url: CONSULTAITON_URL,
    body: {
        ...CONSULTATION,
        users: [
            ...CONSULTATION.users,
            {
                id: 2,
                email: "admin@example.com",
                is_staff: true,
                created_at: "2026-01-29T14:15:50.850685Z",
            }
        ]
    },
}

export const sameUserMock = {
    url: CONSULTAITON_URL,
    body: {
        ...CONSULTATION,
        created_by: {
            email: USER_EMAIL,
        }
    },
}

export const knownUserMock = {
    url: CONSULTAITON_URL,
    body: {
        ...CONSULTATION,
        created_by: {
            email: "another@email.com",
        }
    },
}

export const userMock = {
    url: USER_URL,
    body: USER,
}