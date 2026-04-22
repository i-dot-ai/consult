import { Routes } from "../../../global/routes";

export const defaultMock = {
  url: Routes.ApiUsers,
  method: "POST",
  body: ({ body }: { body: unknown }) => alert("POST request sent with body: \n" + body),
};
