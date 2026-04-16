const URL = `/api/users/test-user/`;

export const getMock = {
  url: URL,
  body: {
    "id": 1,
    "email": "email@example.com",
    "is_staff": true,
    "created_at": "2026-01-29T14:15:50.850685Z"
  }
}

export const patchMock = {
  url: URL,
  method: "PATCH",
}