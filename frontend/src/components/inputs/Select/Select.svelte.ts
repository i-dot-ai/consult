import type { SelectOption } from "../../../global/types";

export interface LabelConfig {
  text: string;
  classes?: string;
}

export interface SelectProps {
  id: string;
  name?: string;
  label?: string | LabelConfig;
  hideLabel?: boolean;
  items: SelectOption[];
  value?: string;
  disabled?: boolean;
  errorMessage?: string;
  hint?: string;
  onchange?: (value: string) => void;
}

export type SelectComponent = typeof import("./Select.svelte").default;