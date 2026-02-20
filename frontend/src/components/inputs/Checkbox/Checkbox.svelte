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
    size?: "xs" | "sm" | "md" | "lg";
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
    size = "md",
    onchange,
  }: Props = $props();

  let labelText = $derived(typeof label === "string" ? label : label?.text);
  let labelClasses = $derived(typeof label === "object" ? label?.classes : "");

  // Convert GOV.UK label classes to Tailwind equivalents
  let tailwindLabelClasses = $derived(
    clsx([
      "text-base leading-5 text-neutral-900 md:text-lg md:leading-6",
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

  <div class="flex items-center gap-3">
    <input
      type="checkbox"
      class={clsx([
        "mt-0.5 rounded border border-neutral-300 bg-white text-neutral-900",
        "focus:border-transparent focus:outline-none focus:ring-2 focus:ring-yellow-400",
        "shrink-0 disabled:cursor-not-allowed disabled:opacity-50",
        "checked:border-primary checked:bg-primary",
        size === "xs" && "h-3 w-3",
        size === "sm" && "h-4 w-4",
        size === "md" && "h-5 w-5",
        size === "lg" && "h-6 w-6",
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
