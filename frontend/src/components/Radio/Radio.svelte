<script lang="ts">
  import type { RadioItem } from "../../global/types";

  interface Props {
    name: string;
    items: RadioItem[];
    value?: string;
    legend?: string;
    onchange?: (value: string) => void;
  }

  let { name, items, value = "", legend, onchange }: Props = $props();

  function handleChange(event: Event) {
    const target = event.target as HTMLInputElement;
    if (onchange) {
      onchange(target.value);
    }
  }

  $effect(() => {
    if (!value && items.length > 0) {
      const checkedItem = items.find(item => item.checked);
      if (checkedItem) {
        value = checkedItem.value;
      }
    }
  });
</script>

<div class="govuk-form-group">
  {#if legend}
    <fieldset class="govuk-fieldset">
      <legend class="govuk-fieldset__legend govuk-fieldset__legend--m">
        <h2 class="govuk-fieldset__heading">
          {legend}
        </h2>
      </legend>
      <div class="govuk-radios">
        {#each items as item}
          <div class="govuk-radios__item">
            <input
              class="govuk-radios__input"
              id="{name}-{item.value}"
              {name}
              type="radio"
              value={item.value}
              checked={value === item.value || (value === "" && item.checked)}
              disabled={item.disabled}
              onchange={handleChange}
            />
            <label class="govuk-label govuk-radios__label" for="{name}-{item.value}">
              {item.text}
            </label>
          </div>
        {/each}
      </div>
    </fieldset>
  {:else}
    <div class="govuk-radios">
      {#each items as item}
        <div class="govuk-radios__item">
          <input
            class="govuk-radios__input"
            id="{name}-{item.value}"
            {name}
            type="radio"
            value={item.value}
            checked={value === item.value || (value === "" && item.checked)}
            disabled={item.disabled}
            onchange={handleChange}
          />
          <label class="govuk-label govuk-radios__label" for="{name}-{item.value}">
            {item.text}
          </label>
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .govuk-form-group {
    margin-bottom: 20px;
  }

  .govuk-fieldset {
    margin: 0;
    padding: 0;
    border: 0;
  }

  .govuk-fieldset__legend {
    font-family: "GDS Transport", arial, sans-serif;
    font-weight: 400;
    font-size: 18px;
    line-height: 1.11111;
    color: #0b0c0c;
    margin-bottom: 15px;
  }

  .govuk-fieldset__legend--m {
    font-size: 18px;
    line-height: 1.11111;
  }

  .govuk-fieldset__heading {
    margin: 0;
    font-size: inherit;
    line-height: inherit;
  }

  .govuk-radios {
    font-family: "GDS Transport", arial, sans-serif;
    font-weight: 400;
    font-size: 16px;
    line-height: 1.25;
    color: #0b0c0c;
  }

  .govuk-radios__item {
    position: relative;
    min-height: 40px;
    margin-bottom: 10px;
    padding-left: 40px;
    clear: left;
  }

  .govuk-radios__item:last-child {
    margin-bottom: 0;
  }

  .govuk-radios__input {
    position: absolute;
    z-index: 1;
    top: -2px;
    left: -2px;
    width: 44px;
    height: 44px;
    margin: 0;
    opacity: 0;
    cursor: pointer;
  }

  .govuk-radios__label {
    display: inline-block;
    margin-bottom: 0;
    padding: 8px 15px 5px;
    cursor: pointer;
    -ms-touch-action: manipulation;
    touch-action: manipulation;
  }

  .govuk-radios__label:before {
    content: "";
    box-sizing: border-box;
    position: absolute;
    top: 0;
    left: 0;
    width: 40px;
    height: 40px;
    border: 2px solid currentColor;
    border-radius: 50%;
    opacity: 1;
    background: transparent;
  }

  .govuk-radios__label:after {
    content: "";
    position: absolute;
    top: 10px;
    left: 10px;
    width: 0;
    height: 0;
    border: 10px solid currentColor;
    border-radius: 50%;
    opacity: 0;
    background: currentColor;
  }

  .govuk-radios__input:checked + .govuk-radios__label:after {
    opacity: 1;
  }

  .govuk-radios__input:focus + .govuk-radios__label:before {
    border-width: 4px;
    box-shadow: 0 0 0 (4px - 2px) #fd0;
  }

  .govuk-radios__input:disabled {
    cursor: default;
  }

  .govuk-radios__input:disabled + .govuk-radios__label {
    opacity: 0.5;
    cursor: default;
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

  @media (min-width: 40.0625em) {
    .govuk-fieldset__legend--m {
      font-size: 24px;
      line-height: 1.04167;
    }

    .govuk-radios {
      font-size: 19px;
      line-height: 1.31579;
    }

    .govuk-label {
      font-size: 19px;
      line-height: 1.31579;
    }
  }
</style>