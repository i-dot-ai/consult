export interface RadioItem {
  value: string;
  text: string;
  checked?: boolean;
  disabled?: boolean;
}

export interface RadioProps {
  name: string;
  items: RadioItem[];
  value?: string;
  legend?: string;
  onchange?: (value: string) => void;
}

export type RadioComponent = typeof import("./Radio.svelte").default;
