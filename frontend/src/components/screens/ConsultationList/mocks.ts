import { consultationsQueryParts } from "../../../global/queries/consultations/parts";

const URL = consultationsQueryParts.url();
const CONSULTATIONS = [
  {
    id: "95ab7567-9381-48eb-8d20-ddeb43691b58",
    title: "Dummy Consultation at Analysis Stage",
    code: "",
    stage: "analysis",
    users: [
      {
        id: 1,
        email: "email@example.com",
        is_staff: true,
        created_at: "2026-01-29T14:15:50.850685Z",
      },
    ],
    created_at: "2026-01-29T14:23:14.719743Z",
  },
  {
    id: "4d1414d5-9300-447b-b788-50d0bef7e807",
    title: "Dummy Consultation at Theme Sign Off Stage",
    code: "",
    stage: "theme_sign_off",
    users: [
      {
        id: 1,
        email: "email@example.com",
        is_staff: true,
        created_at: "2026-01-29T14:15:50.850685Z",
      },
    ],
    created_at: "2026-01-29T14:23:12.423686Z",
  },
];

export const defaultMock = {
  url: URL,
  body: {
    count: 2,
    next: null,
    previous: null,
    results: CONSULTATIONS,
  },
};

export const emptyMock = {
  url: URL,
  body: {
    count: 0,
    next: null,
    previous: null,
    results: [],
  },
};

export const longMock = {
  url: URL,
  body: {
    count: 2,
    next: null,
    previous: null,
    results: Array(100)
      .fill(CONSULTATIONS.at(0))
      .map((item, index) => ({
        ...item,
        id: (index + 1).toString(),
      })),
  },
};
