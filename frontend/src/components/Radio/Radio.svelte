<script lang="ts">
  import clsx from "clsx";
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
      const checkedItem = items.find((item) => item.checked);
      if (checkedItem) {
        value = checkedItem.value;
      }
    }
  });
</script>

<div class="mb-5">
  {#if legend}
    <fieldset class="m-0 p-0 border-0">
      <legend class="text-lg leading-tight text-neutral-900 mb-4 md:text-2xl">
        <h2 class="m-0 text-inherit leading-inherit">
          {legend}
        </h2>
      </legend>
      <div class="text-base leading-5 text-neutral-900 md:text-lg md:leading-6">
        {#each items as item (item.value)}
          <div class="flex items-start gap-3 mb-2.5 last:mb-0">
            <input
              class={clsx([
                "mt-1 h-5 w-5 rounded-full border-2 border-neutral-900 text-neutral-900",
                "focus:ring-2 focus:ring-yellow-400 focus:ring-offset-0",
                "disabled:opacity-50 disabled:cursor-default",
              ])}
              id="{name}-{item.value}"
              {name}
              type="radio"
              value={item.value}
              checked={value === item.value || (value === "" && item.checked)}
              disabled={item.disabled}
              onchange={handleChange}
            />
            <label
              class={clsx([
                "cursor-pointer text-base leading-5 text-neutral-900 md:text-lg md:leading-6",
                item.disabled && "opacity-50 cursor-default",
              ])}
              for="{name}-{item.value}"
            >
              {item.text}
            </label>
          </div>
        {/each}
      </div>
    </fieldset>
  {:else}
    <div class="text-base leading-5 text-neutral-900 md:text-lg md:leading-6">
      {#each items as item (item.value)}
        <div class="flex items-start gap-3 mb-2.5 last:mb-0">
          <input
            class={clsx([
              "mt-1 h-5 w-5 rounded-full border-2 border-neutral-900 text-neutral-900",
              "focus:ring-2 focus:ring-yellow-400 focus:ring-offset-0",
              "disabled:opacity-50 disabled:cursor-default",
            ])}
            id="{name}-{item.value}"
            {name}
            type="radio"
            value={item.value}
            checked={value === item.value || (value === "" && item.checked)}
            disabled={item.disabled}
            onchange={handleChange}
          />
          <label
            class={clsx([
              "cursor-pointer text-base leading-5 text-neutral-900 md:text-lg md:leading-6",
              item.disabled && "opacity-50 cursor-default",
            ])}
            for="{name}-{item.value}"
          >
            {item.text}
          </label>
        </div>
      {/each}
    </div>
  {/if}
</div>
