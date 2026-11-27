<script lang="ts">
  // Using melt-ui popover
  // Docs: https://www.melt-ui.com/docs/builders/popover

  import clsx from "clsx";

  import { createPopover, createSync, melt } from "@melt-ui/svelte";

  import { fade } from "svelte/transition";

  import MaterialIcon from "../../MaterialIcon.svelte";
  import KeyboardArrowDown from "../../svg/material/KeyboardArrowDown.svelte";

  export let label: string = "";
  export let open: boolean = false;
  export let arrow: boolean = true;
  export let border: boolean = true;
  export let handleOpenChange: (next: boolean) => void = () => {};

  const {
    elements: { trigger, content },
    states,
  } = createPopover({
    forceVisible: true,
    onOpenChange: ({ next }) => {
      handleOpenChange(next);
      return next;
    },
  });

  const sync = createSync(states);
  $: sync.open(open, (value) => (open = value));
</script>

<button
  use:melt={$trigger}
  class={clsx([
    "trigger",
    "w-full",
    "p-2",
    "bg-white",
    border && clsx(["border", "border-text-light-95"]),
    "rounded-sm",
  ])}
  title={label || undefined}
  aria-label={label}
>
  <div class="flex items-center justify-between">
    <slot name="trigger" />

    {#if arrow}
      <div
        class={clsx(["transition-transform", "-rotate-90", open && "rotate-0"])}
      >
        <MaterialIcon color="fill-text-light-25">
          <KeyboardArrowDown />
        </MaterialIcon>
      </div>
    {/if}
  </div>
</button>

{#if open}
  <div
    use:melt={$content}
    transition:fade={{ duration: 100 }}
    class=" content bg-text-light-80"
  >
    <slot name="panel" />
  </div>
{/if}

<style lang="postcss">
  @reference "../../../styles/global.css";

  .input {
    @apply flex h-8 w-full rounded-md border border-text-dark-50 bg-transparent px-2.5 text-sm;
    @apply ring-offset-text-light-50 focus-visible:ring;
    @apply focus-visible:ring-text-light-25 focus-visible:ring-offset-1;
    @apply flex-1 items-center justify-center;
    @apply px-2.5 text-sm leading-none text-text-dark-25;
  }

  .trigger {
    /* @apply inline-flex items-center justify-center; */
    @apply text-sm font-medium text-text-dark-50 transition-colors hover:bg-text-light-80;
    @apply focus-visible:ring-3 focus-visible:ring-text-light-25 focus-visible:ring-offset-2;
  }

  .close {
    @apply absolute right-1.5 top-1.5 flex h-7 w-7 items-center justify-center rounded-full;
    @apply text-text-dark-50 transition-colors hover:bg-text/10;
    @apply focus-visible:ring-3 focus-visible:ring-text-light-25 focus-visible:ring-offset-2;
    @apply bg-white p-0 text-sm font-medium;
  }

  .content {
    @apply z-10 rounded-[4px];
  }
</style>
