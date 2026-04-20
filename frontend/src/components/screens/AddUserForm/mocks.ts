import { Routes } from "../../../global/routes";

export const defaultMock = {
  url: Routes.ApiUsers,
  method: "POST",
  callback: ({ options }: { options: {body: string}}) => {
    alert("POST request sent with body: \n" + options.body );
  },
}