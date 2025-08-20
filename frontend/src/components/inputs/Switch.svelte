<script lang="ts">
    import { createSwitch, melt } from '@melt-ui/svelte';

    let {
        id = "",
        label = "",
        value = false,
        handleChange = (newValue: boolean) => {},
    } = $props();

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

<div class="flex items-center justify-around flex-wrap gap-1">
    <label
      class="pr-4 leading-none text-neutral-800 cursor-pointer"
      for={id}
      id={`${id}-label`}
    >
        {#if $$slots.label}
            <slot name="label" />
        {:else}
            {label}
        {/if}
    </label>

    <button
        use:melt={$root}
        class="relative cursor-pointer rounded-full bg-neutral-300 transition-colors data-[state=checked]:bg-neutral-800 shrink-0 data-[state=checked]:hover:bg-neutral-600 hover:bg-neutral-400"
        id={id}
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

  :global([data-state='checked']) .thumb {
    transform: translateX(calc(var(--w) - var(--size) - var(--padding)));
  }
</style>