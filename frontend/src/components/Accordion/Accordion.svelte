<script lang="ts">
  import clsx from "clsx";

  import { slide } from "svelte/transition";
  import { type Component, type Snippet } from "svelte";

  import Button from "../inputs/Button/Button.svelte";
  import MaterialIcon from "../MaterialIcon.svelte";
  import ChevronRight from "../svg/material/ChevronRight.svelte";
  import Close from "../svg/material/Close.svelte";

  export interface Props {
    title: Snippet;
    content: Snippet;
    variant?: "light" | "gray" | "gray-white" | "warning" | "ghost";
    Icon?: Component;
    onClose?: () => void;
    onClick?: () => void;
    ariaLabel?: string;
    initialExpanded?: boolean;
  }

  let {
    title,
    content,
    variant = "light",
    Icon,
    onClose,
    onClick,
    ariaLabel,
    initialExpanded,
  }: Props = $props();

  let expanded = $state(initialExpanded);

  function getButtonVariant() {
    if (variant === "gray") {
      return "gray";
    }
    if (variant === "warning") {
      return "warning";
    }
    if (variant === "ghost") {
      return "gray";
    }
    return "default";
  }

  export function open() {
    expanded = true;
  }

  export function close() {
    expanded = false;
  }
</script>

<Button
  variant={getButtonVariant()}
  handleClick={() => {
    expanded = !expanded;

    if (onClick) {
      onClick();
    }
  }}
  fullWidth={true}
  {ariaLabel}
>
  <div class="flex w-full items-center justify-between gap-2">
    <div class={clsx(["flex", "gap-1", "items-center"])}>
      {#if Icon}
        <div class={clsx(["self-start", "shrink-0", "my-2.5", "mx-1"])}>
          <MaterialIcon
            color={variant === "warning"
              ? "fill-warning"
              : "fill-text-dark-25"}
            size="1.2rem"
          >
            <Icon />
          </MaterialIcon>
        </div>
      {/if}

      {@render title()}
    </div>

    <div
      class={clsx([
        "flex",
        "items-center",
        "gap-0.5",
        "shrink-0",
        "mx-1",
        Icon && clsx(["my-2.5", "self-start"]),
      ])}
    >
      <div class={clsx(["transition-transform", expanded && "rotate-90"])}>
        <MaterialIcon
          color={variant === "warning" ? "fill-warning" : "fill-text"}
        >
          <ChevronRight />
        </MaterialIcon>
      </div>

      {#if onClose}
        <Button
          handleClick={(e) => {
            e.stopPropagation();
            onClose();
          }}
          variant="ghost"
          ariaLabel={`close ${ariaLabel || "accordion"}`}
        >
          <MaterialIcon
            color={variant === "warning"
              ? "fill-warning"
              : "fill-text"}
          >
            <Close />
          </MaterialIcon>
        </Button>
      {/if}
    </div>
  </div>
</Button>

{#if expanded && content}
  <div
    transition:slide
    class={clsx([
      variant === "light" && "bg-white border-text-light-50 p-4",
      variant === "gray" && "bg-text-light-95 border-text-light-50 p-4",
      variant === "gray-white" && "bg-text-light-95 border-text-light-50 p-4",
      variant === "warning" && "bg-warning-light-95 border-warning-light-50 p-4",
      variant === "ghost" && "bg-transparent border-transparent p-0 pt-2",
      "rounded-b-lg border border-t-0",
    ])}
  >
    {@render content()}
  </div>
{/if}
