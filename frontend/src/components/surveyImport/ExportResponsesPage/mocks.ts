import { consultationV2QueryParts } from "../../../global/queries/consultations/parts";

export const CONSULTATION_ID = "95ab7567-9381-48eb-8d20-ddeb43691b58";

export const updateMock = {
  url: consultationV2QueryParts.url(CONSULTATION_ID),
  method: "PATCH",
  body: {
    id: CONSULTATION_ID,
    title: "Heat network zoning",
    data_source: "qualtrics",
  },
};

export const updateErrorMock = {
  ...updateMock,
  status: 400,
  body: { data_source: ['"typeform" is not a valid choice.'] },
};
