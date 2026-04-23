import { getApiFindThemesUrl } from "../../../global/routes";

export const CONSULTATION_ID = "folder1";

export const findMock = {
  url: getApiFindThemesUrl(CONSULTATION_ID),
  method: "POST",
}