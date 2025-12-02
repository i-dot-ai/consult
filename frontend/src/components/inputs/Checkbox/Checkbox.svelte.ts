export interface LabelConfig {
  text: string;
  classes?: string;
}

export interface CheckboxProps {
  id: string;
  name?: string;
  label?: string | LabelConfig;
  hideLabel?: boolean;
  value?: string;
  checked?: boolean;
  disabled?: boolean;
  errorMessage?: string;
  hint?: string;
  onchange?: (checked: boolean, value?: string) => void;
}

export type CheckboxComponent = typeof import("./Checkbox.svelte").default;
