export const lookupMock = {
  url: /\/api\/v2\/consultations\/\?title__iexact=.*/,
  body: {
    results: [
      {
        id: "95ab7567-9381-48eb-8d20-ddeb43691b58",
        title: "Some Existing Consultation",
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
      },
    ],
  },
};

export const consultationsMock = {
  url: "/api/v2/consultations/",
  method: "POST",
  body: {
    id: "95ab7567-9381-48eb-8d20-ddeb43691b58",
    title: "New Consultation",
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
  },
};
