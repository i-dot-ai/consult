<script lang="ts">
  import clsx from "clsx";
  import type { CheckboxItem } from "../../../global/types";

  interface LegendConfig {
    text: string;
    isPageHeading?: boolean;
    classes?: string;
  }

  interface FieldsetConfig {
    legend?: LegendConfig;
  }

  interface Props {
    name: string;
    fieldset?: FieldsetConfig;
    items: CheckboxItem[];
    values?: string[];
    disabled?: boolean;
    errorMessage?: string;
    hint?: string;
    onchange?: (values: string[]) => void;
  }

  let {
    name,
    fieldset,
    items,
    values = [],
    disabled = false,
    errorMessage,
    hint,
    onchange
  }: Props = $props();

  let legendText = $derived(fieldset?.legend?.text);
  let legendClasses = $derived(fieldset?.legend?.classes || '');
  let isPageHeading = $derived(fieldset?.legend?.isPageHeading || false);
  
  // Convert GOV.UK legend classes to Tailwind equivalents
  let tailwindLegendClasses = $derived(
    clsx([
      "text-neutral-900",
      legendClasses?.includes('govuk-fieldset__legend--s') && "text-lg leading-tight md:text-xl font-semibold",
      legendClasses?.includes('govuk-fieldset__legend--m') && "text-xl leading-tight md:text-2xl font-semibold",
      legendClasses?.includes('govuk-fieldset__legend--l') && "text-2xl leading-tight md:text-4xl font-semibold",
      legendClasses?.includes('govuk-fieldset__legend--xl') && "text-3xl leading-tight md:text-5xl font-semibold",
      !legendClasses && "text-base leading-5 md:text-lg md:leading-6"
    ])
  );

  function handleCheckboxChange(event: Event, itemValue: string) {
    if (!onchange) return;
    
    const target = event.target as HTMLInputElement;
    let newValues: string[];
    
    if (target.checked) {
      newValues = [...values, itemValue];
    } else {
      newValues = values.filter(v => v !== itemValue);
    }
    
    onchange(newValues);
  }

  function isChecked(itemValue: string): boolean {
    return values.includes(itemValue);
  }
</script>

<div class={clsx([
  "mb-5",
  errorMessage && "mr-4 border-l-4 border-red-600 pl-3"
])}>
  <fieldset class="border-0 m-0 p-0 min-w-0">
    {#if legendText}
      {#if isPageHeading}
        <legend class={tailwindLegendClasses}>
          <h1 class="m-0 p-0 font-inherit text-inherit">
            {legendText}
          </h1>
        </legend>
      {:else}
        <legend class={tailwindLegendClasses}>
          {legendText}
        </legend>
      {/if}
    {/if}
    
    {#if hint}
      <div id="{name}-hint" class="text-base leading-5 text-neutral-600 mb-4 md:text-lg md:leading-6">
        {hint}
      </div>
    {/if}
    
    {#if errorMessage}
      <p id="{name}-error" class="font-bold text-base leading-5 text-red-600 mb-4 md:text-lg md:leading-6">
        <span class="sr-only">Error:</span> {errorMessage}
      </p>
    {/if}
    
    <div class="space-y-3">
      {#each items as item}
        <div class="flex items-start gap-3">
          <input
            type="checkbox"
            class={clsx([
              "w-5 h-5 mt-0.5 border border-neutral-300 bg-white text-neutral-900 rounded",
              "focus:outline-none focus:ring-2 focus:ring-yellow-400 focus:border-transparent",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              "checked:bg-primary checked:border-primary",
              errorMessage && "border-red-600"
            ])}
            id={`${name}-${item.value}`}
            name={name}
            value={item.value}
            checked={isChecked(item.value)}
            disabled={disabled || item.disabled}
            aria-describedby={[hint && `${name}-hint`, errorMessage && `${name}-error`].filter(Boolean).join(' ') || undefined}
            onchange={(event) => handleCheckboxChange(event, item.value)}
          />
          
          <label 
            class={clsx([
              "text-neutral-900 text-base leading-5 md:text-lg md:leading-6 cursor-pointer select-none",
              (disabled || item.disabled) && "opacity-50 cursor-not-allowed"
            ])} 
            for={`${name}-${item.value}`}
          >
            {item.text}
            {#if item.hint}
              <div class="text-sm leading-4 text-neutral-600 mt-1 md:text-base md:leading-5">
                {item.hint}
              </div>
            {/if}
          </label>
        </div>
      {/each}
    </div>
  </fieldset>
</div>