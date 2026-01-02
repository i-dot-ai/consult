import { type Snippet } from "svelte";

export interface DetailsProps {
  summaryText: string;
  children: Snippet;
  open?: boolean;
}

export type DetailsComponent = typeof import("./Details.svelte").default;
