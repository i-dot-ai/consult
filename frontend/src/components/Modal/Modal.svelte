<script lang="ts">
  import clsx from "clsx";

  import { type Component, type Snippet } from "svelte";
  import { fade, fly } from "svelte/transition";

  import { createDialog, melt } from "@melt-ui/svelte";

  import Button from "../inputs/Button/Button.svelte";
  import MaterialIcon from "../MaterialIcon.svelte";

  import type { MouseEventHandler } from "svelte/elements";

  export interface Props {
    variant?: "primary" | "secondary" | "warning";
    title?: string;
    confirmText?: string;
    confirmDisabled?: boolean;
    canCancel?: boolean;
    canConfirm?: boolean;
    Icon?: Component;
    compact?: boolean;
    open?: boolean;
    setOpen?: (newValue: boolean) => void;
    handleConfirm?: MouseEventHandler<HTMLElement>;
    children?: Snippet;
  }

  let {
    variant = "primary",
    title = "",
    open = false,
    confirmText = "Confirm",
    confirmDisabled = false,
    canCancel = true,
    canConfirm = true,
    Icon,
    compact = false,
    setOpen = () => {},
    handleConfirm = () => {},
    children,
  }: Props = $props();

  const {
    elements: { portalled, overlay, content, title: titleMelt, close },
    states: { open: meltOpen },
  } = createDialog({
    onOpenChange: (open) => {
      setOpen(open.next);
      return open.next;
    },
  });

  $effect(() => {
    meltOpen.set(open);
  });

  const CONFIRM_VARIANTS = {
    primary: "primary",
    secondary: "approve",
    warning: "danger",
  } as const;

  export const getIconColor = () => {
    if (variant === "primary") {
      return "fill-primary";
    }
    if (variant === "secondary") {
      return "fill-secondary";
    }
    if (variant === "warning") {
      return "fill-orange-600";
    }
    return "fill-neutral-500";
  };
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
        compact
          ? [
              "max-w-md",
              "max-h-[86vh]",
              "overflow-y-auto",
              "flex",
              "flex-col",
              "gap-3",
              "p-7",
            ]
          : ["md:max-w-[50vw]", "p-6"],
        "rounded-xl",
        "bg-white",
        "shadow-lg",
      ])}
      transition:fly={{
        duration: 150,
        y: 8,
      }}
    >
      <div class={clsx(["flex", "items-center", "gap-2", !compact && "mb-2"])}>
        {#if Icon}
          <MaterialIcon color={getIconColor()} size="1.3rem">
            <Icon />
          </MaterialIcon>
        {/if}
        <h3
          use:melt={$titleMelt}
          class={clsx(
            compact
              ? ["text-base", "font-medium", "text-neutral-900"]
              : [
                  "text-lg",
                  variant === "secondary" && "text-secondary",
                  variant === "warning" && "text-orange-600",
                ],
          )}
        >
          {title}
        </h3>
      </div>

      {#if children}
        {@render children()}
      {/if}

      <footer class="flex items-center justify-end gap-2">
        {#if canCancel}
          <div use:melt={$close}>
            <Button size="sm">Cancel</Button>
          </div>
        {/if}

        {#if canConfirm}
          <Button
            size="sm"
            variant={CONFIRM_VARIANTS[variant]}
            handleClick={handleConfirm as () => void}
            disabled={confirmDisabled}
          >
            {confirmText}
          </Button>
        {/if}
      </footer>
    </div>
  </div>
{/if}
