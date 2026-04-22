import { Routes } from "../../../global/routes";

export const defaultMock = {
  url: Routes.ApiUsers,
  method: "POST",
  callback: ({ body }: { body?: BodyInit | null }) => {
    alert("POST request sent with body: \n" + body);
  },
};
