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

export const STRUCTURE_CHECK_IDS = {
  noMergedCells: "user-no-merged-cells",
} as const;

export const CONTENT_CHECK_IDS = {
  responsesMerged: "user-responses-merged",
  demographicColumns: "user-demographic-columns",
  piiRemoved: "user-pii-removed",
} as const;

export const PROVIDER_CHECK_LABELS: Record<DataSource, string> = {
  "citizen-space":
    "Row 1 holds the question wording, as Citizen Space exports it",
  qualtrics: "Rows 1 to 3 hold the question details, as Qualtrics exports them",
};

export const ROW_STRUCTURE_LABEL: Record<DataSource, string> = {
  "citizen-space":
    "From row 2, each row is one person's complete response, with one question per column",
  qualtrics:
    "From row 4, each row is one person's complete response, with one question per column",
};

export const STRUCTURE_CHECK_LABELS: Record<
  keyof typeof STRUCTURE_CHECK_IDS,
  string
> = {
  noMergedCells: "No merged cells",
};

export const CONTENT_CHECK_LABELS: Record<
  keyof typeof CONTENT_CHECK_IDS,
  string
> = {
  responsesMerged:
    "Responses from email and other channels are in this one file",
  demographicColumns: "Demographic columns are kept, not deleted",
  piiRemoved:
    "Personal information is removed, where your department needs it removed",
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
    label:
      "Responses with only demographic answers, or none, are removed and counted",
  },
];
