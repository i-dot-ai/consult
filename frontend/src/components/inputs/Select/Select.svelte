<script lang="ts">
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
    errorMessage,
    hint,
    onchange
  }: Props = $props();

  let labelText = $derived(typeof label === 'string' ? label : label?.text);
  let labelClasses = $derived(typeof label === 'object' ? label?.classes : '');

  function handleChange(event: Event) {
    const target = event.target as HTMLSelectElement;
    if (onchange) {
      onchange(target.value);
    }
  }
</script>

<div class="govuk-form-group" class:govuk-form-group--error={errorMessage}>
  {#if labelText && !hideLabel}
    <label class="govuk-label {labelClasses}" for={id}>
      {labelText}
    </label>
  {/if}
  
  {#if hint}
    <div id="{id}-hint" class="govuk-hint">
      {hint}
    </div>
  {/if}
  
  {#if errorMessage}
    <p id="{id}-error" class="govuk-error-message">
      <span class="govuk-visually-hidden">Error:</span> {errorMessage}
    </p>
  {/if}
  
  <select
    class="govuk-select"
    class:govuk-select--error={errorMessage}
    {id}
    {name}
    {value}
    {disabled}
    aria-describedby={[hint && `${id}-hint`, errorMessage && `${id}-error`].filter(Boolean).join(' ') || undefined}
    onchange={handleChange}
  >
    {#each items as item}
      <option value={item.value} selected={value === item.value}>
        {item.label}
      </option>
    {/each}
  </select>
</div>

<style>
  .govuk-form-group {
    margin-bottom: 20px;
  }

  .govuk-form-group--error {
    margin-right: 15px;
    border-left: 5px solid #d4351c;
    padding-left: 10px;
  }

  .govuk-label {
    font-family: "GDS Transport", arial, sans-serif;
    font-weight: 400;
    font-size: 16px;
    line-height: 1.25;
    color: #0b0c0c;
    display: block;
    margin-bottom: 5px;
  }

  .govuk-label--s {
    font-weight: 600;
  }

  .govuk-label--m {
    font-size: 18px;
    line-height: 1.11111;
    font-weight: 600;
  }

  .govuk-label--l {
    font-size: 24px;
    line-height: 1.04167;
    font-weight: 600;
  }

  .govuk-label--xl {
    font-size: 32px;
    line-height: 1.09375;
    font-weight: 600;
  }

  .govuk-hint {
    font-family: "GDS Transport", arial, sans-serif;
    font-weight: 400;
    font-size: 16px;
    line-height: 1.25;
    color: #505a5f;
    margin-bottom: 15px;
  }

  .govuk-error-message {
    font-family: "GDS Transport", arial, sans-serif;
    font-weight: 700;
    font-size: 16px;
    line-height: 1.25;
    color: #d4351c;
    margin-bottom: 15px;
  }

  .govuk-visually-hidden {
    position: absolute !important;
    width: 1px !important;
    height: 1px !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
    clip: rect(0 0 0 0) !important;
    -webkit-clip-path: inset(50%) !important;
    clip-path: inset(50%) !important;
    border: 0 !important;
    white-space: nowrap !important;
  }

  .govuk-select {
    font-family: "GDS Transport", arial, sans-serif;
    font-weight: 400;
    font-size: 16px;
    line-height: 1.25;
    box-sizing: border-box;
    width: 100%;
    height: 40px;
    margin-top: 0;
    padding: 5px 4px 4px;
    border: rgb(209 213 219 / var(--tw-border-opacity, 1)) 1px solid;
    border-radius: 0;
    -webkit-appearance: menulist;
    -moz-appearance: menulist;
    appearance: menulist;
    background-color: #ffffff;
    color: #0b0c0c;
  }

  .govuk-select:focus {
    outline: 3px solid #fd0;
    outline-offset: 0;
    box-shadow: inset 0 0 0 2px;
  }

  .govuk-select:disabled {
    opacity: 0.5;
    color: #505a5f;
    background-color: #f3f2f1;
    cursor: not-allowed;
  }

  .govuk-select--error {
    border-color: #d4351c;
  }

  .govuk-select option {
    color: #0b0c0c;
    background-color: #ffffff;
  }

  @media (min-width: 40.0625em) {
    .govuk-label {
      font-size: 19px;
      line-height: 1.31579;
    }

    .govuk-label--m {
      font-size: 24px;
      line-height: 1.04167;
    }

    .govuk-label--l {
      font-size: 36px;
      line-height: 1.11111;
    }

    .govuk-label--xl {
      font-size: 48px;
      line-height: 1.04167;
    }

    .govuk-hint {
      font-size: 19px;
      line-height: 1.31579;
    }

    .govuk-error-message {
      font-size: 19px;
      line-height: 1.31579;
    }

    .govuk-select {
      font-size: 19px;
      line-height: 1.31579;
    }
  }
</style>