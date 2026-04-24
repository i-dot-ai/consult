import { getApiAssignThemesUrl } from "../../../global/routes";

export const CONSULTATION_ID = "folder1";

export const assignMock = {
  url: getApiAssignThemesUrl(CONSULTATION_ID),
  method: "POST",
}