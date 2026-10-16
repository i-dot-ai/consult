<script lang="ts" generics="T extends string">
  import clsx from "clsx";

  import MaterialIcon from "../../MaterialIcon.svelte";
  import Check from "../../svg/material/Check.svelte";

  interface RadioCardItem {
    value: T;
    text: string;
    hint?: string;
  }

  interface Props {
    name: string;
    legend: string;
    hint?: string;
    items: RadioCardItem[];
    value: T;
    onchange: (value: T) => void;
  }

  let { name, legend, hint, items, value, onchange }: Props = $props();
</script>

<fieldset class="m-0 border-0 p-0">
  <legend class="text-base leading-tight text-neutral-900 md:text-lg">
    <h2 class="leading-inherit m-0 text-inherit">{legend}</h2>
  </legend>

  {#if hint}
    <p class="mt-1 text-sm text-neutral-500">{hint}</p>
  {/if}

  <div class="mt-4 flex flex-wrap gap-3">
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
            "flex w-56 cursor-pointer items-center justify-between gap-3",
            "rounded-lg border px-4 py-3 transition-colors",
            checked
              ? "border-yellow-400 bg-neutral-50 ring-2 ring-yellow-400"
              : "border-neutral-300 bg-white hover:border-neutral-400",
            "peer-focus-visible:ring-2 peer-focus-visible:ring-yellow-400 peer-focus-visible:ring-offset-2",
          ])}
        >
          <span class="flex flex-col">
            <span class="text-sm text-neutral-900">{item.text}</span>
            {#if item.hint}
              <span class="text-xs text-neutral-500">{item.hint}</span>
            {/if}
          </span>
          {#if checked}
            <MaterialIcon size="1rem" color="fill-neutral-900">
              <Check />
            </MaterialIcon>
          {/if}
        </label>
      </div>
    {/each}
  </div>
</fieldset>
