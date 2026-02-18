<script lang="ts">
  import clsx from "clsx";
  import type { SelectOption } from "../../../global/types";

  interface LabelConfig {
    text: string;
    classes?: string;
  }

  interface Props {
    id: string;
    name?: string;
    label?: string | LabelConfig;
    hideLabel?: boolean;
    items: SelectOption[];
    value?: string;
    disabled?: boolean;
    required?: boolean;
    errorMessage?: string;
    hint?: string;
    onchange?: (value: string) => void;
  }

  let {
    id,
    name = id,
    label,
    hideLabel = false,
    items,
    value = "",
    disabled = false,
    required = false,
    errorMessage,
    hint,
    onchange,
  }: Props = $props();

  let labelText = $derived(typeof label === "string" ? label : label?.text);
  let labelClasses = $derived(typeof label === "object" ? label?.classes : "");

  // Convert GOV.UK label classes to Tailwind equivalents
  let tailwindLabelClasses = $derived(
    clsx([
      "mb-1 block text-base leading-5 text-neutral-900 md:text-lg md:leading-6",
      labelClasses?.includes("govuk-label--s") && "font-semibold",
      labelClasses?.includes("govuk-label--m") &&
        "text-lg font-semibold leading-tight md:text-2xl",
      labelClasses?.includes("govuk-label--l") &&
        "text-2xl font-semibold leading-tight md:text-4xl",
      labelClasses?.includes("govuk-label--xl") &&
        "text-3xl font-semibold leading-tight md:text-5xl",
    ]),
  );

  function handleChange(event: Event) {
    const target = event.target as HTMLSelectElement;
    if (onchange) {
      onchange(target.value);
    }
  }
</script>

<div
  class={clsx([errorMessage && "mr-4 border-l-4 border-red-600 pl-3"])}
>
  {#if labelText && !hideLabel}
    <label class={tailwindLabelClasses} for={id}>
      {labelText}
    </label>
  {/if}

  {#if hint}
    <div
      id="{id}-hint"
      class="mb-4 text-base leading-5 text-neutral-600 md:text-lg md:leading-6"
    >
      {hint}
    </div>
  {/if}

  {#if errorMessage}
    <p
      id="{id}-error"
      class="mb-4 text-base font-bold leading-5 text-red-600 md:text-lg md:leading-6"
    >
      <span class="sr-only">Error:</span>
      {errorMessage}
    </p>
  {/if}

  <select
    class={clsx([
      "w-full min-h-[38px] rounded-sm border border-gray-300 bg-white p-1 text-neutral-700",
      "focus:outline-2 focus:outline-yellow-300",
      "disabled:cursor-not-allowed disabled:bg-neutral-100 disabled:text-neutral-600 disabled:opacity-50",
      errorMessage && "border-red-600",
    ])}
    {id}
    {name}
    {value}
    {disabled}
    {required}
    aria-describedby={[hint && `${id}-hint`, errorMessage && `${id}-error`]
      .filter(Boolean)
      .join(" ") || undefined}
    onchange={handleChange}
  >
    {#each items as item (item.value)}
      <option
        value={item.value}
        selected={value === item.value}
        class="bg-white text-neutral-900"
      >
        {item.label}
      </option>
    {/each}
  </select>
</div>
