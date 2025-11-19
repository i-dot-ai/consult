import type { CheckboxItem } from "../../../global/types";

export interface LegendConfig {
  text: string;
  isPageHeading?: boolean;
  classes?: string;
}

export interface FieldsetConfig {
  legend?: LegendConfig;
}

export interface CheckboxGroupProps {
  name: string;
  fieldset?: FieldsetConfig;
  items: CheckboxItem[];
  values?: string[];
  disabled?: boolean;
  errorMessage?: string;
  hint?: string;
  onchange?: (values: string[]) => void;
}

export type CheckboxGroupComponent = typeof import("./CheckboxGroup.svelte").default;