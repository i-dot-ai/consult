<script lang="ts">
  import clsx from "clsx";

  import type { Snippet } from "svelte";
  import { fade, fly } from "svelte/transition";
  import type { MouseEventHandler } from "svelte/elements";

  import { createDialog, melt } from '@melt-ui/svelte';
  
  import Button from "../inputs/Button/Button.svelte";


  interface Props {
    open: boolean;
    confirmText: string;
    setOpen: (newValue: boolean) => void;
    handleConfirm: MouseEventHandler<any>;
    children: Snippet;
  }

  let {
    open = false,
    confirmText = "Confirm",
    setOpen = () => {},
    handleConfirm = () => {},
    children,
  }: Props = $props();

  const {
    elements: { trigger, portalled, overlay, content, title, description, close },
    states: { open: meltOpen }
  } = createDialog({
    onOpenChange: (open) => setOpen(open.next),
  });

  $effect(() => {
    meltOpen.set(open);
  });
</script>

{#if $meltOpen}
  <div use:melt={$portalled}>
    <div
      use:melt={$overlay}
      transition:fade={{ duration: 150 }}
      class="fixed inset-0 z-50 bg-black/50"
    ></div>

    <div
      use:melt={$content}
      class={clsx([
        "fixed",
        "left-1/2",
        "top-1/2",
        "z-50",
        "-translate-x-1/2",
        "-translate-y-1/2",
        "w-[90vw]",
        "md:max-w-[50vw]",
        "p-6",
        "rounded-xl",
        "bg-white",
        "shadow-lg",
      ])}
      transition:fly={{
        duration: 150,
        y: 8,
      }}
    >
      {@render children()}

      <footer class="flex items-center justify-end gap-2">
        <div use:melt={$close}>
          <Button size="sm">
            Cancel
          </Button>
        </div>
        
        <Button size="sm" variant="primary" handleClick={handleConfirm}>
          {confirmText}
        </Button>
      </footer>
    </div>
  </div>
{/if}