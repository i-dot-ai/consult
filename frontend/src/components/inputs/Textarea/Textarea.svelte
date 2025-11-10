<script lang="ts">
  import clsx from "clsx";

  export interface Props {
    id: string;
    label?: string;
    hideLabel?: boolean;
    rows?: number;
    placeholder?: string;
    value: string;
    setValue: (newValue: string) => void;
  }

  let {
    id = "",
    label = "",
    hideLabel = false,
    rows = 3,
    placeholder = "",
    value = "",
    setValue = () => {},
  }: Props = $props();
</script>

<div>
  <label for={id} class={clsx([hideLabel && "sr-only"])}>
    {label}
  </label>

  <textarea
    {id}
    style={`min-height: ${rows}lh;`}
    class={clsx([
      "block",
      "w-full",
      "mt-1",
      "p-1",
      "border",
      "border-gray-300",
      "rounded-sm",
      "focus:outline-2 focus:outline-yellow-300",
    ])}
    {placeholder}
    {rows}
    {value}
    oninput={(e) => setValue((e.target as HTMLTextAreaElement).value)}
  ></textarea>
</div>
