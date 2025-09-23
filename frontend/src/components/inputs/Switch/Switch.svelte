<script lang="ts">
  // Using melt-ui switch
  // Docs: https://www.melt-ui.com/docs/builders/switch

  import clsx from "clsx";

  import { createSwitch, melt } from "@melt-ui/svelte";

  interface Props {
    id: string;
    label: string;
    hideLabel?: boolean;
    value: boolean;
    handleChange: (newValue: boolean) => void;
  }

  let {
    id = "",
    label = "",
    hideLabel = false,
    value = false,
    handleChange = () => {},
  }: Props = $props();

  const {
    elements: { root, input },
    states: { checked },
  } = createSwitch({
    onCheckedChange: ({ curr, next }) => {
      handleChange(next);
      return next;
    },
  });

  $effect(() => checked.set(value));
</script>

<div
  class={clsx([
    "flex",
    "items-center",
    !hideLabel && "justify-around",
    "flex-wrap",
    "gap-1",
  ])}
>
  {#if !hideLabel}
    <label
      class="grow pr-4 leading-none text-neutral-800 cursor-pointer"
      for={id}
      id={`${id}-label`}
    >
      {#if $$slots.label}
        <slot name="label" />
      {:else}
        {label}
      {/if}
    </label>
  {/if}

  <button
    use:melt={$root}
    class={clsx([
      "relative",
      "cursor-pointer",
      "rounded-full",
      "bg-neutral-300",
      "transition-colors",
      "data-[state=checked]:bg-neutral-800",
      "shrink-0",
      "data-[state=checked]:hover:bg-neutral-600",
      "hover:bg-neutral-400",
    ])}
    {id}
    aria-labelledby={`${id}-label`}
  >
    <span class="thumb block rounded-full bg-white transition"></span>
  </button>

  <input use:melt={$input} />
</div>

<style>
  button {
    --w: 2rem;
    --h: 1rem;
    --padding: 0.125rem;
    width: var(--w);
    height: var(--h);
  }

  .thumb {
    --size: 0.75rem;
    width: var(--size);
    height: var(--size);
    transform: translateX(var(--padding));
  }

  :global([data-state="checked"]) .thumb {
    transform: translateX(calc(var(--w) - var(--size) - var(--padding)));
  }
</style>
