import { Routes } from "../../routes";

export const currentUserGetQueryParts = {
  key: () => ["currentUser"],
  url: () => Routes.ApiCurrentUser,
};
