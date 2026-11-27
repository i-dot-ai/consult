<script module lang="ts">
  export interface RadioCardItem<Value extends string = string> {
    value: Value;
    text: string;
    hint?: string;
  }
</script>

<script lang="ts" generics="T extends string">
  import clsx from "clsx";

  import MaterialIcon from "../../MaterialIcon.svelte";
  import Check from "../../svg/material/Check.svelte";

  interface Props {
    name: string;
    legend: string;
    hint?: string;
    items: RadioCardItem<T>[];
    value: T;
    onchange: (value: T) => void;
  }

  let { name, legend, hint, items, value, onchange }: Props = $props();
</script>

<fieldset class="m-0 border-0 p-0">
  <legend class="text-base leading-tight font-medium text-text-dark-50">
    <h2 class="leading-inherit m-0 text-inherit">{legend}</h2>
  </legend>

  {#if hint}
    <p class="mt-1 text-sm text-text">{hint}</p>
  {/if}

  <div class="mt-4 grid gap-2.5 sm:grid-cols-2">
    {#each items as item (item.value)}
      {@const id = `${name}-${item.value}`}
      {@const checked = value === item.value}

      <div>
        <input
          class="peer sr-only"
          {id}
          {name}
          type="radio"
          value={item.value}
          {checked}
          onchange={() => onchange(item.value)}
        />
        <label
          for={id}
          class={clsx([
            "flex cursor-pointer items-end justify-between gap-3",
            "rounded-lg border px-3.5 py-4 text-sm transition-colors",
            // ring-inset thickens the selected border without resizing the card
            checked
              ? "border-text-dark-50 bg-text-light-95 ring-1 ring-text-dark-50 ring-inset"
              : "border-text-light-50 bg-white hover:bg-text-light-95",
            "peer-focus-visible:outline-3 peer-focus-visible:outline-warning peer-focus-visible:outline-offset-0",
          ])}
        >
          <span class="flex flex-col">
            <span class="text-text-dark-50">{item.text}</span>
            {#if item.hint}
              <span class="mt-0.5 text-xs text-text">{item.hint}</span>
            {/if}
          </span>
          {#if checked}
            <MaterialIcon color="fill-text-dark-50" size="1rem">
              <Check />
            </MaterialIcon>
          {/if}
        </label>
      </div>
    {/each}
  </div>
</fieldset>
