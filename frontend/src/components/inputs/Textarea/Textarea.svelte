<script lang="ts">
  import clsx from "clsx";

  import { cssVars } from "../../../global/actions";

  export interface Props {
    id: string;
    label?: string;
    hideLabel?: boolean;
    hint?: string;
    errorMessage?: string;
    rows?: number;
    placeholder?: string;
    value: string;
    setValue: (newValue: string) => void;
    disabled?: boolean;
  }

  let {
    id = "",
    label = "",
    hideLabel = false,
    hint = "",
    errorMessage = "",
    rows = 3,
    placeholder = "",
    value = "",
    setValue = () => {},
    disabled = false,
  }: Props = $props();

  let describedBy = $derived(
    [hint && `${id}-hint`, errorMessage && `${id}-error`]
      .filter(Boolean)
      .join(" ") || undefined,
  );
</script>

<div>
  <label for={id} class={clsx([hideLabel && "sr-only"])}>
    {label}
  </label>

  {#if hint}
    <p id={`${id}-hint`} class="mt-1 text-sm text-neutral-500">{hint}</p>
  {/if}

  {#if errorMessage}
    <p id={`${id}-error`} class="mt-1 text-sm font-bold text-red-600">
      {errorMessage}
    </p>
  {/if}

  <textarea
    {id}
    use:cssVars={{ "textarea-min-height": `${rows}lh` }}
    class={clsx([
      "block",
      "w-full",
      "min-h-(--textarea-min-height)",
      "mt-1",
      "p-1",
      "border",
      errorMessage ? "border-red-600" : "border-gray-300",
      "rounded-xs",
      "focus:outline-2 focus:outline-yellow-300",
    ])}
    {placeholder}
    {rows}
    {value}
    {disabled}
    aria-describedby={describedBy}
    aria-invalid={errorMessage ? true : undefined}
    oninput={(e) => setValue((e.target as HTMLTextAreaElement).value)}
  ></textarea>
</div>
