import type { DataSource } from "../../../global/queries/consultations/types";

export interface Check {
  id: string;
  label: string;
  hint?: string;
}

export const PROVIDER_CHECKS: Record<DataSource, Check[]> = {
  "citizen-space": [
    {
      id: "cs-row-structure",
      label:
        "Row 1 contains question text, row 2 onwards contains one response per row",
    },
  ],
  qualtrics: [
    {
      id: "qualtrics-row-structure",
      label:
        "Rows 1–3 contain question and metadata headers, row 4 onwards contains one response per row",
      hint: "Qualtrics exports include three header rows: question text, question ID, and ImportId.",
    },
  ],
};

export const USER_CHECKS: Check[] = [
  {
    id: "user-one-question-per-column",
    label:
      "Each column contains one question, each row contains one set of responses",
  },
  {
    id: "user-pii-removed",
    label: "All personally identifiable information (PII) has been removed",
    hint: "This includes names, email addresses, phone numbers, home addresses, IP addresses, and any other data that could identify an individual.",
  },
  {
    id: "user-responses-merged",
    label:
      "Responses from other sources (e.g. emails) have been merged into a single file",
  },
  {
    id: "user-file-type",
    label: "The file is .xlsx or .csv",
  },
  {
    id: "user-no-merged-cells",
    label: "There are no merged cells in the file",
    hint: "Merged cells will be split during processing — only the top-left cell retains its value.",
  },
  {
    id: "user-demographic-columns",
    label: "Demographic columns have not been removed",
  },
];

export const TECHNICAL_CHECKS: Check[] = [
  {
    id: "tech-headers-complete",
    label:
      "Row 1 contains text in every column that has data in the rows below",
  },
  {
    id: "tech-no-formulas",
    label: "No calculations or formulas exist in the file",
    hint: "Cells should contain plain values only. Convert any Excel formulas to their static results before uploading.",
  },
  {
    id: "tech-no-merged-cells",
    label: "No merged cells exist in the file",
  },
  {
    id: "tech-file-type",
    label: "The file is .xlsx or .csv",
  },
  {
    id: "tech-no-special-characters",
    label: "No special non-printing characters are present",
    hint: "This refers to ASCII control characters (e.g. null bytes, escape characters). Standard symbols like & are fine.",
  },
  {
    id: "tech-no-empty-rows",
    label: "No entirely empty rows exist within the response data",
    hint: "Blank rows between responses can disrupt processing. Rows at the very end of the file are fine.",
  },
];
