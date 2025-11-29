<script lang="ts">
  import clsx from "clsx";

  interface LabelConfig {
    text: string;
    classes?: string;
  }

  interface Props {
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

  let {
    id,
    name = id,
    label,
    hideLabel = false,
    value,
    checked = false,
    disabled = false,
    errorMessage,
    hint,
    onchange,
  }: Props = $props();

  let labelText = $derived(typeof label === "string" ? label : label?.text);
  let labelClasses = $derived(typeof label === "object" ? label?.classes : "");

  // Convert GOV.UK label classes to Tailwind equivalents
  let tailwindLabelClasses = $derived(
    clsx([
      "text-neutral-900 text-base leading-5 md:text-lg md:leading-6",
      labelClasses?.includes("govuk-label--s") && "font-semibold",
      labelClasses?.includes("govuk-label--m") &&
        "text-lg leading-tight md:text-2xl font-semibold",
      labelClasses?.includes("govuk-label--l") &&
        "text-2xl leading-tight md:text-4xl font-semibold",
      labelClasses?.includes("govuk-label--xl") &&
        "text-3xl leading-tight md:text-5xl font-semibold",
    ]),
  );

  function handleChange(event: Event) {
    const target = event.target as HTMLInputElement;
    if (onchange) {
      onchange(target.checked, value);
    }
  }
</script>

<div
  class={clsx(["mb-5", errorMessage && "mr-4 border-l-4 border-red-600 pl-3"])}
>
  {#if hint}
    <div
      id="{id}-hint"
      class="text-base leading-5 text-neutral-600 mb-4 md:text-lg md:leading-6"
    >
      {hint}
    </div>
  {/if}

  {#if errorMessage}
    <p
      id="{id}-error"
      class="font-bold text-base leading-5 text-red-600 mb-4 md:text-lg md:leading-6"
    >
      <span class="sr-only">Error:</span>
      {errorMessage}
    </p>
  {/if}

  <div class="flex items-center gap-3">
    <input
      type="checkbox"
      class={clsx([
        "w-5 h-5 mt-0.5 border border-neutral-300 bg-white text-neutral-900 rounded",
        "focus:outline-none focus:ring-2 focus:ring-yellow-400 focus:border-transparent",
        "disabled:opacity-50 disabled:cursor-not-allowed shrink-0",
        "checked:bg-primary checked:border-primary",
        errorMessage && "border-red-600",
      ])}
      {id}
      {name}
      {value}
      {checked}
      {disabled}
      aria-describedby={[hint && `${id}-hint`, errorMessage && `${id}-error`]
        .filter(Boolean)
        .join(" ") || undefined}
      onchange={handleChange}
    />

    {#if labelText && !hideLabel}
      <label
        class={clsx([tailwindLabelClasses, "cursor-pointer select-none"])}
        for={id}
      >
        {labelText}
      </label>
    {/if}
  </div>
</div>
