import type { DataSource } from "../../../../global/queries/consultations/types";
import type { Snippet } from "svelte";

export interface Check {
  id: string;
  label: string;
  example?: Snippet;
}

export const PROVIDER_CHECK_IDS = {
  citizenSpaceRowStructure: "cs-row-structure",
  qualtricsRowStructure: "qualtrics-row-structure",
} as const;

export const USER_CHECK_IDS = {
  rowStructure: "user-row-structure",
  noMergedCells: "user-no-merged-cells",
  fileType: "user-file-type",
  responsesMerged: "user-responses-merged",
  demographicColumns: "user-demographic-columns",
  piiRemoved: "user-pii-removed",
} as const;

export const PROVIDER_CHECK_LABELS: Record<DataSource, string> = {
  "citizen-space": "Row 1 holds the question wording, as Citizen Space exports it",
  qualtrics: "Rows 1 to 3 hold the question details, as Qualtrics exports them",
};

export const USER_CHECK_LABELS: Record<keyof typeof USER_CHECK_IDS, string> = {
  rowStructure: "From row 4, each row is one person's complete response, with one question per column",
  noMergedCells: "No merged cells",
  fileType: "The file is a .csv or .xlsx",
  responsesMerged: "Responses from email and other channels are in this one file",
  demographicColumns: "Demographic columns are kept, not deleted",
  piiRemoved: "Personal information is removed, where your department needs it removed",
};

export const TECHNICAL_CHECKS: Omit<Check, "example">[] = [
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
    label: "Responses with only demographic answers, or none, are removed and counted",
  },
];
