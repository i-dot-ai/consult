<script lang="ts">
  import clsx from "clsx";

  import { type Snippet } from "svelte";

  import { createPopover, melt } from "@melt-ui/svelte";

  import Button from "../../inputs/Button/Button.svelte";
  import MaterialIcon from "../../MaterialIcon.svelte";
  import Help from "../../svg/material/Help.svelte";
  import Close from "../../svg/material/Close.svelte";

  export interface Props {
    direction?: "right" | "left";
    children: Snippet;
  }

  let { direction = "right", children }: Props = $props();
  let isOpen = $state(false);

  const {
    elements: { trigger, content },
  } = createPopover({
    onOpenChange: ({ next }) => {
      isOpen = next;
      return next;
    },
    positioning: {
      placement: "top",
      strategy: "fixed",
      gutter: 10,
      flip: true,
    },
  });
</script>

<div class="relative m-auto max-w-[10rem]">
  <div
    use:melt={$trigger}
    class={clsx([
      "floating-panel",
      "w-max",
      "overflow-hidden",
      "rounded-full",
      "transition-transform",
      "translate-x-0",
      direction === "left" &&
        "has-[button[aria-pressed=true]]:-translate-x-[8rem]",
      direction === "right" &&
        "has-[button[aria-pressed=true]]:translate-x-[8rem]",
    ])}
  >
    <Button
      variant="ghost"
      highlighted={isOpen}
      handleClick={() => {
        isOpen = !isOpen;
      }}
      noPadding={true}
      highlightVariant="approve"
      fixedHoverColor={true}
    >
      <div
        class={clsx([
          "rounded-full",
          "bg-secondary",
          "p-2",
          "transition-all",
          "hover:bg-teal-500",
          "hover:p-2.5",
        ])}
      >
        <MaterialIcon color="fill-white">
          {#if isOpen}
            <Close />
          {:else}
            <Help />
          {/if}
        </MaterialIcon>
      </div>
    </Button>
  </div>

  <div
    use:melt={$content}
    class={clsx([
      "relative",
      "mb-12",
      "border",
      "bg-white",
      "p-2",
      "transition-opacity",
      "shadow-lg",
      "rounded-lg,",
      !isOpen && clsx(["pointer-events-none", "opacity-0"]),
    ])}
  >
    {#if children}
      {@render children()}
    {/if}

    <div class="absolute right-0 top-0 m-4">
      <Button variant="ghost" handleClick={() => (isOpen = false)}>
        <MaterialIcon color="fill-neutral-500">
          <Close />
        </MaterialIcon>
      </Button>
    </div>
  </div>
</div>
