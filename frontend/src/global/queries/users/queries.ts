import { buildQuery } from "../../queryClient";
import { currentUserGetQueryParts } from "./parts";
import { type CurrentUserGetResponse } from "./types";

export function buildCurrentUserGetQuery() {
  return buildQuery<CurrentUserGetResponse>(currentUserGetQueryParts.url(), {
    key: currentUserGetQueryParts.key(),
  });
}
