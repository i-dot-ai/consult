import { getApiUserDetails } from "../../../global/routes";

export const USER = {
  id: "test-user",
  email: "user@test.com",
  is_staff: false,
  created_at: new Date().toISOString(),
}

export const deleteMock = {
  url: getApiUserDetails(USER.id),
  method: "DELETE",
}