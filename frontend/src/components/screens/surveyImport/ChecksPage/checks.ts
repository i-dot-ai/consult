import type { DataSource } from "../../../../global/queries/consultations/types";

export interface Check {
  id: string;
  label: string;
  hint?: string;
}

export const PROVIDER_CHECKS: Record<DataSource, Check[]> = {
  "citizen-space": [
    {
      id: "cs-row-structure",
      label: "Row 1 holds the question wording, as Citizen Space exports it",
    },
  ],
  qualtrics: [
    {
      id: "qualtrics-row-structure",
      label: "Rows 1 to 3 hold the question details, as Qualtrics exports them",
    },
  ],
};

export const USER_CHECKS: Check[] = [
  {
    id: "user-row-structure",
    label:
      "From row 2, each row is one person's complete response, with one question per column",
  },
  {
    id: "user-no-merged-cells",
    label: "No merged cells",
  },
  {
    id: "user-file-type",
    label: "The file is a .csv or .xlsx",
  },
  {
    id: "user-responses-merged",
    label: "Responses from email and other channels are in this one file",
  },
  {
    id: "user-demographic-columns",
    label: "Demographic columns are kept, not deleted",
  },
  {
    id: "user-pii-removed",
    label:
      "Personal information is removed, where your department needs it removed",
  },
];

export const TECHNICAL_CHECKS: Check[] = [
  {
    id: "tech-headers-complete",
    label: "Every column with answers has a question",
  },
  {
    id: "tech-no-formulas",
    label: "No cell holds a formula or calculation",
  },
  {
    id: "tech-no-merged-cells",
    label: "No merged cells. If there are any, the upload stops and says where",
  },
  {
    id: "tech-file-type",
    label: "The file is a .csv or .xlsx",
  },
  {
    id: "tech-no-special-characters",
    label: "No characters Consult cannot read",
  },
  {
    id: "tech-no-empty-rows",
    label:
      "Responses with only demographic answers, or none, are removed and counted",
  },
];
