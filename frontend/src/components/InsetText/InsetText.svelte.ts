import { type Snippet } from "svelte";

export interface InsetTextProps {
  variant?: "default" | "info" | "warning" | "success" | "error";
  className?: string;
  children: Snippet;
}

export type InsetTextComponent = typeof import("./InsetText.svelte").default;
